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


def semantic_model_settings(model_name: str) -> dict[str, Any]:
    config = semantic_config()
    models = config.get("models") or {}
    settings = models.get(model_name) or {}
    if not isinstance(settings, dict):
        raise SystemExit(f"Semantic model settings for `{model_name}` must be an object.")
    defaults = {
        "query_prefix": "",
        "document_prefix": "",
        "query_prompt_name": None,
        "document_prompt_name": None,
        "max_seq_length": None,
        "trust_remote_code": False,
        "device": None,
        "revision": None,
    }
    return {**defaults, **settings}


def semantic_text(block: dict[str, Any], max_chars: int) -> str:
    title = block.get("document_title") or ""
    heading = " ".join(block.get("heading_path") or [])
    number = block.get("number") or ""
    pasal = block.get("pasal") or ""
    ayat = block.get("ayat") or ""
    # The v2 contract keeps a legal node's human-facing excerpt separate from
    # the context used to produce a retrieval representation.
    text = block["retrieval_text"]
    value = " ".join(part for part in (title, heading, number, pasal, ayat, text) if part)
    return value[:max_chars]


@lru_cache(maxsize=2)
def _load_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit("Install semantic dependencies with `uv sync` before using semantic retrieval.") from exc
    settings = semantic_model_settings(model_name)
    load_kwargs: dict[str, Any] = {"trust_remote_code": bool(settings["trust_remote_code"])}
    if settings.get("device"):
        load_kwargs["device"] = settings["device"]
    if settings.get("revision"):
        load_kwargs["revision"] = settings["revision"]
    model = SentenceTransformer(model_name, **load_kwargs)
    if settings.get("max_seq_length"):
        model.max_seq_length = int(settings["max_seq_length"])
    return model


def _role_texts(model_name: str | None, texts: str | list[str], role: str) -> str | list[str]:
    if not model_name:
        return texts
    prefix = str(semantic_model_settings(model_name).get(f"{role}_prefix") or "")
    if not prefix:
        return texts
    if isinstance(texts, str):
        return texts if texts.startswith(prefix) else f"{prefix}{texts}"
    return [text if text.startswith(prefix) else f"{prefix}{text}" for text in texts]


def _encode_role(
    model_name: str | None,
    model: Any,
    texts: str | list[str],
    role: str,
    batch_size: int | None,
    normalize: bool,
    show_progress_bar: bool,
) -> np.ndarray:
    settings = semantic_model_settings(model_name) if model_name else {}
    values = _role_texts(model_name, texts, role)
    prefix = settings.get(f"{role}_prefix") or ""
    prompt_name = settings.get(f"{role}_prompt_name")

    # Explicit prefixes take precedence over model-level prompts so E5 is not
    # accidentally prefixed twice when using encode_query/encode_document.
    if prefix or prompt_name:
        encode = model.encode
        encode_kwargs: dict[str, Any] = {}
        if prompt_name and not prefix:
            encode_kwargs["prompt_name"] = prompt_name
    else:
        encode = getattr(model, "encode_query" if role == "query" else "encode_document", None)
        if encode is None:
            encode = model.encode
        encode_kwargs = {}

    if batch_size is not None:
        encode_kwargs["batch_size"] = batch_size
    return np.asarray(
        encode(
            values,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            **encode_kwargs,
        ),
        dtype=np.float32,
    )


def _encode_documents(
    model: Any,
    texts: list[str],
    batch_size: int,
    normalize: bool,
    model_name: str | None = None,
) -> np.ndarray:
    return _encode_role(
        model_name,
        model,
        texts,
        "document",
        batch_size,
        normalize,
        show_progress_bar=True,
    )


def _encode_query(
    model: Any,
    query: str,
    normalize: bool,
    model_name: str | None = None,
) -> np.ndarray:
    return _encode_role(
        model_name,
        model,
        query,
        "query",
        None,
        normalize,
        show_progress_bar=False,
    )


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
    embeddings = _encode_documents(model, texts, batch_size, normalize, model_name=model_name)
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
        "model_settings": semantic_model_settings(model_name),
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
    model_name = str(metadata["model_name"])
    if metadata.get("model_settings") != semantic_model_settings(model_name):
        print("Warning: semantic model encoding settings changed; rebuild the index before searching.")
    query_embedding = _encode_query(
        model,
        query,
        bool(metadata.get("normalize_embeddings", True)),
        model_name=model_name,
    )
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
    limit = int(args.limit if args.limit is not None else semantic_config().get("default_limit", 10))
    results = semantic_search(
        args.query,
        limit,
        issuer=args.issuer,
        role=args.role,
        source=args.source,
        include_secondary=args.include_secondary,
    )
    from .lexical import format_search_results

    print(format_search_results(args.query, results))
