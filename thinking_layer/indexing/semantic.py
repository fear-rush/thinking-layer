from __future__ import annotations

import argparse
import json
from functools import lru_cache
from typing import Any

import numpy as np

from ..common.io import iter_ndjson_file, read_json
from ..config.heuristics import load_heuristic_config
from ..config.paths import (
    ROOT,
    SEMANTIC_INDEX_DIR,
    SEMANTIC_INDEX_DOCS,
    SEMANTIC_INDEX_EMBEDDINGS,
    SEMANTIC_INDEX_METADATA,
    SOURCE_CORPUS_PATH,
)
from .lexical import index_signature, load_search_blocks


def semantic_config() -> dict[str, Any]:
    return load_heuristic_config("semantic_retrieval")


def semantic_text(block: dict[str, Any], max_chars: int) -> str:
    title = block.get("document_title") or ""
    heading = " ".join(block.get("heading_path") or [])
    number = block.get("number") or ""
    pasal = block.get("pasal") or ""
    ayat = block.get("ayat") or ""
    text = block.get("text") or ""
    value = " ".join(part for part in (title, heading, number, pasal, ayat, text) if part)
    return value[:max_chars]


@lru_cache(maxsize=2)
def _load_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit("Install semantic dependencies with `uv sync` before using semantic retrieval.") from exc
    return SentenceTransformer(model_name)


def _encode_documents(model: Any, texts: list[str], batch_size: int, normalize: bool) -> np.ndarray:
    encode_document = getattr(model, "encode_document", None)
    if encode_document is None:
        encode_document = model.encode
    return np.asarray(
        encode_document(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
        ),
        dtype=np.float32,
    )


def _encode_query(model: Any, query: str, normalize: bool) -> np.ndarray:
    encode_query = getattr(model, "encode_query", None)
    if encode_query is None:
        encode_query = model.encode
    return np.asarray(
        encode_query(query, convert_to_numpy=True, normalize_embeddings=normalize),
        dtype=np.float32,
    )


def semantic_index_exists() -> bool:
    return all(path.exists() for path in (SEMANTIC_INDEX_METADATA, SEMANTIC_INDEX_EMBEDDINGS, SEMANTIC_INDEX_DOCS))


def semantic_index_metadata() -> dict[str, Any]:
    if not SEMANTIC_INDEX_METADATA.exists():
        raise SystemExit("Missing semantic index. Run `build-semantic-index` first.")
    return read_json(SEMANTIC_INDEX_METADATA)


def build_semantic_index(
    model_name: str,
    limit: int | None = None,
    batch_size: int | None = None,
    normalize: bool | None = None,
) -> dict[str, Any]:
    config = semantic_config()
    model_name = model_name or str(config.get("default_model"))
    batch_size = int(batch_size or config.get("batch_size", 32))
    normalize = bool(config.get("normalize_embeddings", True) if normalize is None else normalize)
    max_chars = int(config.get("max_text_chars", 6000))
    blocks = load_search_blocks(None, None, None, include_secondary=True)
    if limit:
        blocks = blocks[:limit]
    if not blocks:
        raise SystemExit("No source-corpus blocks available for semantic indexing.")

    model = _load_model(model_name)
    texts = [semantic_text(block, max_chars) for block in blocks]
    embeddings = _encode_documents(model, texts, batch_size, normalize)
    if embeddings.ndim != 2 or len(embeddings) != len(blocks):
        raise SystemExit(f"Unexpected embedding shape: {embeddings.shape}")

    SEMANTIC_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    np.save(SEMANTIC_INDEX_EMBEDDINGS, embeddings)
    with SEMANTIC_INDEX_DOCS.open("w", encoding="utf-8") as handle:
        for block in blocks:
            handle.write(json.dumps(block, ensure_ascii=False) + "\n")

    metadata = {
        "model_name": model_name,
        "normalize_embeddings": normalize,
        "embedding_dimension": int(embeddings.shape[1]),
        "block_count": len(blocks),
        "batch_size": batch_size,
        "max_text_chars": max_chars,
        "corpus_signature": index_signature(),
        "source_corpus": str(SOURCE_CORPUS_PATH.relative_to(ROOT)) if SOURCE_CORPUS_PATH.exists() else None,
    }
    SEMANTIC_INDEX_METADATA.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def load_semantic_blocks() -> list[dict[str, Any]]:
    return list(iter_ndjson_file(SEMANTIC_INDEX_DOCS))


def semantic_search(
    query: str,
    limit: int = 10,
    issuer: str | None = None,
    role: str | None = None,
    source: str | None = None,
    include_secondary: bool = True,
) -> list[dict[str, Any]]:
    metadata = semantic_index_metadata()
    if metadata.get("corpus_signature") != index_signature():
        print("Warning: persisted semantic index may be stale; rebuild it before benchmarking.")
    model = _load_model(str(metadata["model_name"]))
    query_embedding = _encode_query(model, query, bool(metadata.get("normalize_embeddings", True)))
    embeddings = np.load(SEMANTIC_INDEX_EMBEDDINGS, mmap_mode="r")
    blocks = load_semantic_blocks()
    if len(embeddings) != len(blocks):
        raise SystemExit("Semantic index embeddings and document metadata have different lengths.")
    if query_embedding.shape[-1] != embeddings.shape[-1]:
        raise SystemExit(
            f"Semantic query dimension {query_embedding.shape[-1]} does not match index dimension {embeddings.shape[-1]}."
        )

    eligible = []
    for index, block in enumerate(blocks):
        if issuer and block.get("issuer") != issuer:
            continue
        if role and block.get("file_role") != role:
            continue
        if source and block.get("source") != source:
            continue
        if not include_secondary and block.get("file_role") in {"secondary_faq", "secondary_summary"}:
            continue
        eligible.append(index)
    if not eligible:
        return []

    scores = embeddings[eligible] @ query_embedding
    result_count = min(limit, len(eligible))
    candidate_positions = np.argpartition(-scores, result_count - 1)[:result_count]
    candidate_positions = candidate_positions[np.argsort(-scores[candidate_positions])]
    results = []
    for position in candidate_positions:
        block = dict(blocks[eligible[int(position)]])
        score = float(scores[int(position)])
        block["_semantic_score"] = score
        block["_score"] = score
        block["_retriever"] = "semantic"
        results.append(block)
    return results


def cmd_build_semantic_index(args: argparse.Namespace) -> None:
    metadata = build_semantic_index(args.model, args.limit, args.batch_size, args.normalize_embeddings)
    print(f"Wrote {SEMANTIC_INDEX_DIR.relative_to(ROOT)}/embeddings.npy")
    print(f"Wrote {SEMANTIC_INDEX_DIR.relative_to(ROOT)}/docs.ndjson")
    print(f"Wrote {SEMANTIC_INDEX_DIR.relative_to(ROOT)}/metadata.json")
    print(f"Blocks: {metadata['block_count']}; dimensions: {metadata['embedding_dimension']}; model: {metadata['model_name']}")


def cmd_semantic_search(args: argparse.Namespace) -> None:
    results = semantic_search(
        args.query,
        args.limit,
        issuer=args.issuer,
        role=args.role,
        source=args.source,
        include_secondary=args.include_secondary,
    )
    from .lexical import format_search_results

    print(format_search_results(args.query, results))
