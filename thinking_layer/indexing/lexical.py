from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from ..config.heuristics import heuristic_section
from ..corpus.citations import citation_quality_for_block
from ..common.io import iter_ndjson_file, read_json, read_ndjson_file
from ..config.paths import PROCESSED_DIR, ROOT, SEARCH_INDEX_DIR, SOURCE_CORPUS_PATH, STOPWORDS_PATH
from ..retrieval.query_tools import contains_pattern, load_stopwords, tokenize, tokenize_with_stopwords
from ..common.text import normalize_space
from .scoring import apply_lexical_boosts, bm25_term_score, candidate_terms_for, query_terms_for, relevant_exact_phrases

@dataclass
class SearchIndex:
    blocks: list[dict[str, Any]]
    doc_terms: list[Counter[str]]
    doc_lengths: list[int]
    doc_freq: Counter[str]
    postings: dict[str, list[int]]
    avg_len: float
    stopwords: set[str]

def load_search_blocks(
    issuer: str | None,
    role: str | None,
    source: str | None,
    include_secondary: bool,
) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    if SOURCE_CORPUS_PATH.exists():
        source_path = SOURCE_CORPUS_PATH
        rows = iter_ndjson_file(source_path)
    else:
        extracted_ok = {
            row["file_id"]
            for row in read_ndjson_file(PROCESSED_DIR / "extracted_documents.ndjson")
            if row.get("extraction_status") == "extracted_ok"
        }
        source_path = PROCESSED_DIR / "blocks.ndjson"
        rows = (row for row in iter_ndjson_file(source_path) if row.get("file_id") in extracted_ok)

    for row in rows:
        if issuer and row.get("issuer", "").lower() != issuer.lower():
            continue
        if role and row.get("file_role") != role:
            continue
        if source and row.get("source") != source:
            continue
        if not include_secondary and row.get("file_role") in {"secondary_faq", "secondary_summary"}:
            continue
        if not row.get("text") or not row.get("page_start"):
            continue
        blocks.append(row)
    return blocks

def build_bm25(blocks: list[dict[str, Any]], stopwords: set[str]) -> tuple[list[Counter[str]], list[int], Counter[str], dict[str, list[int]], float]:
    doc_terms: list[Counter[str]] = []
    doc_lengths: list[int] = []
    doc_freq: Counter[str] = Counter()
    postings: dict[str, list[int]] = defaultdict(list)
    total_len = 0
    for doc_index, block in enumerate(blocks):
        title = block.get("document_title") or ""
        heading = " ".join(block.get("heading_path") or [])
        reg_number = block.get("number") or ""
        weighted_text = " ".join(
            [
                title,
                title,
                title,
                block.get("regulation_type") or "",
                reg_number,
                reg_number,
                heading,
                heading,
                block.get("pasal") or "",
                block.get("ayat") or "",
                block.get("text") or "",
            ]
        )
        terms = Counter(tokenize_with_stopwords(weighted_text, stopwords))
        doc_terms.append(terms)
        doc_len = sum(terms.values())
        doc_lengths.append(doc_len)
        total_len += doc_len
        doc_freq.update(terms.keys())
        for term in terms:
            postings[term].append(doc_index)
    avg_len = total_len / len(blocks) if blocks else 0.0
    return doc_terms, doc_lengths, doc_freq, dict(postings), avg_len

def build_search_index(blocks: list[dict[str, Any]]) -> SearchIndex:
    stopwords = load_stopwords()
    doc_terms, doc_lengths, doc_freq, postings, avg_len = build_bm25(blocks, stopwords)
    return SearchIndex(blocks=blocks, doc_terms=doc_terms, doc_lengths=doc_lengths, doc_freq=doc_freq, postings=postings, avg_len=avg_len, stopwords=stopwords)

def index_signature() -> dict[str, Any]:
    blocks_path = PROCESSED_DIR / "blocks.ndjson"
    extracted_path = PROCESSED_DIR / "extracted_documents.ndjson"
    source_corpus_path = SOURCE_CORPUS_PATH
    corpus_path = source_corpus_path if source_corpus_path.exists() else blocks_path
    return {
        "version": 2,
        "corpus_path": str(corpus_path.relative_to(ROOT)) if corpus_path.exists() else None,
        "corpus_mtime": corpus_path.stat().st_mtime if corpus_path.exists() else None,
        "corpus_size": corpus_path.stat().st_size if corpus_path.exists() else None,
        "source_corpus_mtime": source_corpus_path.stat().st_mtime if source_corpus_path.exists() else None,
        "source_corpus_size": source_corpus_path.stat().st_size if source_corpus_path.exists() else None,
        "blocks_mtime": blocks_path.stat().st_mtime if blocks_path.exists() else None,
        "blocks_size": blocks_path.stat().st_size if blocks_path.exists() else None,
        "extracted_mtime": extracted_path.stat().st_mtime if extracted_path.exists() else None,
        "extracted_size": extracted_path.stat().st_size if extracted_path.exists() else None,
        "stopwords_sha1": hashlib.sha1(STOPWORDS_PATH.read_bytes()).hexdigest() if STOPWORDS_PATH.exists() else None,
    }

def write_search_index(index: SearchIndex, filters: dict[str, Any]) -> None:
    SEARCH_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    docs_path = SEARCH_INDEX_DIR / "docs.ndjson"
    terms_path = SEARCH_INDEX_DIR / "terms.ndjson"
    postings_path = SEARCH_INDEX_DIR / "postings.ndjson"
    metadata_path = SEARCH_INDEX_DIR / "metadata.json"

    with docs_path.open("w", encoding="utf-8") as f:
        for doc_id, (block, doc_len) in enumerate(zip(index.blocks, index.doc_lengths)):
            doc = dict(block)
            doc["_doc_id"] = doc_id
            doc["_doc_len"] = doc_len
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    with terms_path.open("w", encoding="utf-8") as f:
        for doc_id, terms in enumerate(index.doc_terms):
            f.write(json.dumps({"doc_id": doc_id, "terms": dict(terms)}, ensure_ascii=False) + "\n")

    with postings_path.open("w", encoding="utf-8") as f:
        for term, doc_ids in sorted(index.postings.items()):
            f.write(json.dumps({"term": term, "doc_ids": doc_ids}, ensure_ascii=False) + "\n")

    metadata = {
        "signature": index_signature(),
        "filters": filters,
        "doc_count": len(index.blocks),
        "term_count": len(index.doc_freq),
        "avg_len": index.avg_len,
        "doc_freq": dict(index.doc_freq),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def persisted_index_exists() -> bool:
    return all(
        (SEARCH_INDEX_DIR / name).exists()
        for name in ("metadata.json", "docs.ndjson", "terms.ndjson", "postings.ndjson")
    )

@lru_cache(maxsize=1)
def load_persisted_search_index() -> SearchIndex:
    if not persisted_index_exists():
        raise SystemExit("Missing persisted search index. Run `uv run python -m thinking_layer.cli build-index` first.")

    metadata = read_json(SEARCH_INDEX_DIR / "metadata.json")
    current_signature = index_signature()
    if metadata.get("signature") != current_signature:
        print("Warning: persisted search index may be stale. Rebuild with `build-index`.", flush=True)

    blocks: list[dict[str, Any]] = []
    doc_lengths: list[int] = []
    for row in read_ndjson_file(SEARCH_INDEX_DIR / "docs.ndjson"):
        doc_lengths.append(int(row.pop("_doc_len", 0)))
        row.pop("_doc_id", None)
        blocks.append(row)

    doc_terms: list[Counter[str]] = []
    for row in read_ndjson_file(SEARCH_INDEX_DIR / "terms.ndjson"):
        doc_terms.append(Counter(row.get("terms") or {}))

    postings: dict[str, list[int]] = {}
    for row in read_ndjson_file(SEARCH_INDEX_DIR / "postings.ndjson"):
        postings[row["term"]] = row.get("doc_ids") or []

    return SearchIndex(
        blocks=blocks,
        doc_terms=doc_terms,
        doc_lengths=doc_lengths,
        doc_freq=Counter(metadata.get("doc_freq") or {}),
        postings=postings,
        avg_len=float(metadata.get("avg_len") or 0.0),
        stopwords=load_stopwords(),
    )

def get_search_index(
    issuer: str | None = None,
    role: str | None = None,
    source: str | None = None,
    include_secondary: bool = True,
    prefer_persisted: bool = True,
) -> SearchIndex:
    if prefer_persisted and not issuer and not role and not source and include_secondary and persisted_index_exists():
        return load_persisted_search_index()
    blocks = load_search_blocks(issuer, role, source, include_secondary)
    return build_search_index(blocks)

def filter_index(index: SearchIndex, issuer: str | None, role: str | None, source: str | None, include_secondary: bool) -> SearchIndex:
    if not issuer and not role and not source and include_secondary:
        return index
    blocks = []
    for block in index.blocks:
        if issuer and block.get("issuer") != issuer:
            continue
        if role and block.get("file_role") != role:
            continue
        if source and block.get("source") != source:
            continue
        if not include_secondary and block.get("file_role") in {"secondary_faq", "secondary_summary"}:
            continue
        blocks.append(block)
    return build_search_index(blocks)

def bm25_search(query: str, index: SearchIndex, limit: int, issuer: str | None = None) -> list[dict[str, Any]]:
    query_terms = query_terms_for(query, index.stopwords)
    if not query_terms or not index.blocks:
        return []

    total_docs = len(index.blocks)
    scored: list[tuple[float, dict[str, Any]]] = []
    query_counter = Counter(query_terms)
    exact_phrases = relevant_exact_phrases(query)

    candidate_terms = candidate_terms_for(query_terms, index.doc_freq)
    candidate_indexes: set[int] = set()
    for term in candidate_terms:
        candidate_indexes.update(index.postings.get(term, []))

    for doc_index in candidate_indexes:
        block = index.blocks[doc_index]
        terms = index.doc_terms[doc_index]
        if issuer and block.get("issuer") != issuer:
            continue
        doc_len = index.doc_lengths[doc_index] or 1
        score = bm25_term_score(query_counter, terms, index.doc_freq, total_docs, doc_len, index.avg_len)
        if score <= 0:
            continue

        score, matched_phrases = apply_lexical_boosts(score, query, query_terms, index.stopwords, block, exact_phrases)

        if score > 0:
            enriched = dict(block)
            if matched_phrases:
                enriched["_matched_exact_phrases"] = matched_phrases
            enriched["_score"] = score
            scored.append((score, enriched))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item for _, item in scored[:limit]]

def needs_balanced_issuer_search(query: str) -> bool:
    config = heuristic_section("retrieval_ranking", "balanced_issuer_search")
    return contains_pattern(query, str(config.get("ojk_pattern", "ojk"))) and any(
        contains_pattern(query, pattern)
        for pattern in config.get("bi_patterns", ["bi", "bank indonesia"])
    )

def dedupe_results(results: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    seen: set[tuple[Any, Any, Any, Any]] = set()
    deduped: list[dict[str, Any]] = []
    for row in results:
        key = (row.get("document_title"), row.get("page_start"), row.get("pasal"), row.get("text")[:120])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
        if len(deduped) >= limit:
            break
    return deduped

def planned_search(query: str, index: SearchIndex, limit: int) -> list[dict[str, Any]]:
    if not needs_balanced_issuer_search(query):
        return dedupe_results(bm25_search(query, index, limit * 2), limit)

    config = heuristic_section("retrieval_ranking", "balanced_issuer_search")
    per_issuer_limit = max(int(config.get("min_per_issuer_limit", 3)), limit // 2)
    candidate_multiplier = int(config.get("candidate_multiplier", 3))
    bi = bm25_search(query, index, per_issuer_limit * candidate_multiplier, issuer="BI")
    ojk = bm25_search(query, index, per_issuer_limit * candidate_multiplier, issuer="OJK")

    merged: list[dict[str, Any]] = []
    for bucket in (bi[:per_issuer_limit], ojk[:per_issuer_limit]):
        merged.extend(bucket)
    merged.extend(bi[per_issuer_limit:])
    merged.extend(ojk[per_issuer_limit:])
    return dedupe_results(merged, limit)

def snippet(text: str, query: str, max_len: int | None = None) -> str:
    config = heuristic_section("retrieval_ranking", "snippet")
    if max_len is None:
        max_len = int(config.get("max_len", 420))
    text = normalize_space(text)
    query_terms = tokenize(query)
    lower = text.lower()
    positions = [lower.find(term) for term in query_terms if lower.find(term) >= 0]
    if positions:
        start = max(0, min(positions) - int(config.get("context_before_first_match", 120)))
    else:
        start = 0
    value = text[start : start + max_len]
    if start > 0:
        value = "..." + value
    if start + max_len < len(text):
        value += "..."
    return value

def format_search_results(query: str, results: list[dict[str, Any]]) -> str:
    lines = [f"# Search Results: {query}", ""]
    if not results:
        return "\n".join([*lines, "No results found.", ""])

    for index, row in enumerate(results, start=1):
        citation = row.get("citation") or {}
        pasal = citation.get("pasal") or "-"
        ayat = citation.get("ayat") or "-"
        huruf = citation.get("huruf") or "-"
        lines.extend(
            [
                f"## {index}. {row.get('document_title')}",
                "",
                f"- Score: `{row.get('_score'):.3f}`",
                f"- Source: `{row.get('source')}` / `{row.get('issuer')}`",
                f"- Role: `{row.get('file_role')}`",
                f"- Citation: page `{citation.get('page')}`, `{pasal}`, `{ayat}`, `{huruf}`",
                f"- Block type: `{row.get('block_type')}`",
                "",
                snippet(row.get("text") or "", query),
                "",
            ]
        )
    return "\n".join(lines)
