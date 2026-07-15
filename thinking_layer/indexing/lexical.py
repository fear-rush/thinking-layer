from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from ..config.heuristics import heuristic_section
from ..common.io import iter_ndjson_file
from ..config.paths import PROCESSED_DIR, ROOT, SOURCE_CORPUS_PATH, STOPWORDS_PATH
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
    if not SOURCE_CORPUS_PATH.exists():
        raise SystemExit(
            "Missing processed/source_corpus.ndjson. "
            "Run `uv run python -m thinking_layer.cli build-source-corpus --include-secondary` first."
        )
    rows = iter_ndjson_file(SOURCE_CORPUS_PATH)

    for row in rows:
        if issuer and row.get("issuer", "").lower() != issuer.lower():
            continue
        if role and row.get("file_role") != role:
            continue
        if source and row.get("source") != source:
            continue
        if not include_secondary and row.get("file_role") in {"secondary_faq", "secondary_summary"}:
            continue
        if not row.get("retrieval_text") or not row.get("page_start"):
            continue
        blocks.append(row)
    return blocks


def load_search_blocks_from_offset(
    offset: int,
    issuer: str | None,
    role: str | None,
    source: str | None,
    include_secondary: bool,
) -> list[dict[str, Any]]:
    """Load only appended source-corpus rows after a known byte offset."""
    if not SOURCE_CORPUS_PATH.exists():
        return []
    blocks: list[dict[str, Any]] = []
    with SOURCE_CORPUS_PATH.open("rb") as handle:
        handle.seek(offset)
        for raw_line in handle:
            if not raw_line.strip():
                continue
            row = json.loads(raw_line.decode("utf-8"))
            if issuer and row.get("issuer", "").lower() != issuer.lower():
                continue
            if role and row.get("file_role") != role:
                continue
            if source and row.get("source") != source:
                continue
            if not include_secondary and row.get("file_role") in {"secondary_faq", "secondary_summary"}:
                continue
            if not row.get("retrieval_text") or not row.get("page_start"):
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
        # Legal nodes keep the human-facing excerpt separate from the
        # contextual representation used for matching.
        body_text = block["retrieval_text"]
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
                body_text,
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


def append_search_index(index: SearchIndex, blocks: list[dict[str, Any]]) -> SearchIndex:
    """Extend an index with new blocks without retokenizing existing blocks."""
    if not blocks:
        return index
    added = build_search_index(blocks)
    offset = len(index.blocks)
    index.blocks.extend(added.blocks)
    index.doc_terms.extend(added.doc_terms)
    index.doc_lengths.extend(added.doc_lengths)
    index.doc_freq.update(added.doc_freq)
    for term, doc_ids in added.postings.items():
        index.postings.setdefault(term, []).extend(offset + doc_id for doc_id in doc_ids)
    old_count = offset
    new_count = len(index.blocks)
    index.avg_len = (
        ((index.avg_len * old_count) + (added.avg_len * len(added.blocks))) / new_count
        if new_count
        else 0.0
    )
    return index

def index_signature() -> dict[str, Any]:
    blocks_path = PROCESSED_DIR / "blocks.ndjson"
    extracted_path = PROCESSED_DIR / "extracted_documents.ndjson"
    source_corpus_path = SOURCE_CORPUS_PATH
    if not source_corpus_path.exists():
        raise FileNotFoundError(
            "Missing processed/source_corpus.ndjson. "
            "Run `uv run python -m thinking_layer.cli build-source-corpus --include-secondary` first."
        )
    corpus_path = source_corpus_path
    return {
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


def source_state() -> dict[str, Any]:
    """Return append-detection metadata for the source corpus."""
    corpus_path = SOURCE_CORPUS_PATH
    if not corpus_path.exists():
        return {"path": None, "size": None, "prefix_sha1": None}
    size = corpus_path.stat().st_size
    digest = hashlib.sha1()
    with corpus_path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return {
        "path": str(corpus_path.relative_to(ROOT)),
        "size": size,
        "prefix_sha1": digest.hexdigest(),
    }


def sha1_prefix(path, length: int) -> str:
    digest = hashlib.sha1()
    remaining = length
    with path.open("rb") as handle:
        while remaining:
            chunk = handle.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()

def get_search_index(
    issuer: str | None = None,
    role: str | None = None,
    source: str | None = None,
    include_secondary: bool = True,
    prefer_persisted: bool = True,
) -> SearchIndex:
    # Kept as an API-compatible argument for callers that previously selected
    # the removed JSON index. In-memory indexes are now built only from the
    # canonical source corpus; production retrieval uses SQLite directly.
    _ = prefer_persisted
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

def bm25_search(
    query: str,
    index: SearchIndex,
    limit: int,
    issuer: str | None = None,
    file_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
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
        if file_ids and block.get("file_id") not in file_ids:
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

def planned_search(query: str, index: SearchIndex, limit: int, file_ids: set[str] | None = None) -> list[dict[str, Any]]:
    if not needs_balanced_issuer_search(query):
        return dedupe_results(bm25_search(query, index, limit * 2, file_ids=file_ids), limit)

    config = heuristic_section("retrieval_ranking", "balanced_issuer_search")
    per_issuer_limit = max(int(config.get("min_per_issuer_limit", 3)), limit // 2)
    candidate_multiplier = int(config.get("candidate_multiplier", 3))
    bi = bm25_search(query, index, per_issuer_limit * candidate_multiplier, issuer="BI", file_ids=file_ids)
    ojk = bm25_search(query, index, per_issuer_limit * candidate_multiplier, issuer="OJK", file_ids=file_ids)

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
