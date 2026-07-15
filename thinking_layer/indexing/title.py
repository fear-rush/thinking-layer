from __future__ import annotations

from typing import Any

from ..config.heuristics import heuristic_section
from ..corpus.citations import citation_quality_for_block
from ..retrieval.query_tools import tokenize_with_stopwords
from ..common.text import normalize_space
from .lexical import SearchIndex, relevant_exact_phrases

TITLE_SEARCH_MIN_SCORE = float(heuristic_section("retrieval_ranking", "title_search").get("min_score", 65.0))


def longest_shared_token_run(left: list[str], right: list[str]) -> int:
    """Return the longest contiguous token phrase shared by two sequences."""

    if not left or not right:
        return 0
    previous = [0] * (len(right) + 1)
    longest = 0
    for left_token in left:
        current = [0] * (len(right) + 1)
        for index, right_token in enumerate(right, start=1):
            if left_token == right_token:
                current[index] = previous[index - 1] + 1
                longest = max(longest, current[index])
        previous = current
    return longest

def document_representative_rank(block: dict[str, Any]) -> tuple[int, int, int, int, int]:
    citation_quality_rank = {
        # For normal entries, keep the most precise legal anchor available.
        # Bounded enumeration aggregates are ranked ahead separately below:
        # they are the only parent-level units admitted by v2 and preserve a
        # governing lead-in plus its immediate list items as one readable
        # answer claim.
        "document_page_pasal_ayat_huruf": 0,
        "document_page_pasal_ayat": 1,
        "document_page_pasal": 2,
        "document_page": 3,
        "document_only": 4,
    }
    block_type_rank = {
        "article": 0,
        "paragraph": 1,
        "heading": 2,
        "list_item": 3,
        "table_or_row": 4,
        "qa_or_faq": 5,
    }
    page = int(block.get("page_start") or block.get("page") or 999999)
    text_len = len(block.get("text") or "")
    return (
        0 if block.get("citation_admission") == "enumeration_aggregate" else 1,
        citation_quality_rank.get(block.get("citation_quality") or citation_quality_for_block(block), 9),
        page,
        block_type_rank.get(block.get("block_type"), 9),
        text_len,
    )

def title_match_score(query: str, title: str, stopwords: set[str]) -> float:
    config = heuristic_section("retrieval_ranking", "title_search")
    query_norm = normalize_space(query).lower()
    title_norm = normalize_space(title).lower()
    if not query_norm or not title_norm:
        return 0.0

    query_tokens = tokenize_with_stopwords(query_norm, stopwords)
    title_tokens = tokenize_with_stopwords(title_norm, stopwords)
    if not query_tokens or not title_tokens:
        return 0.0

    query_set = set(query_tokens)
    title_set = set(title_tokens)
    overlap = query_set & title_set
    if not overlap:
        return 0.0

    coverage = len(overlap) / max(1, len(query_set))
    title_coverage = len(overlap) / max(1, len(title_set))
    score = (
        coverage * float(config.get("coverage_weight", 60.0))
        + title_coverage * float(config.get("title_coverage_weight", 35.0))
        + len(overlap) * float(config.get("overlap_count_weight", 4.0))
    )

    if query_norm == title_norm:
        score += float(config.get("exact_query_bonus", 80.0))
    elif query_norm in title_norm or title_norm in query_norm:
        score += float(config.get("query_title_substring_bonus", 45.0))
    elif all(token in title_set for token in query_set):
        score += float(config.get("all_query_tokens_bonus", 35.0))

    ordered_query = " ".join(query_tokens)
    ordered_title = " ".join(title_tokens)
    if ordered_query and ordered_query in ordered_title:
        score += float(config.get("ordered_query_bonus", 35.0))

    # Natural questions contain verbs and answer-shape words that should not
    # erase a precise document noun phrase.  A contiguous shared phrase such
    # as "pembawaan uang kertas asing" is stronger title evidence than the
    # same tokens scattered across a long title.
    shared_run = longest_shared_token_run(query_tokens, title_tokens)
    if shared_run >= int(config.get("shared_phrase_min_tokens", 3)):
        score += min(
            float(config.get("shared_phrase_max_bonus", 48.0)),
            shared_run * float(config.get("shared_phrase_bonus_per_token", 12.0)),
        )

    if (
        len(title_set) <= int(config.get("short_title_max_tokens", 2))
        and len(query_set) >= int(config.get("long_query_min_tokens", 4))
        and coverage < float(config.get("short_title_min_coverage", 0.75))
    ):
        score *= float(config.get("short_title_penalty_multiplier", 0.55))

    return score

def enrich_title_hit(block: dict[str, Any], score: float, query: str) -> dict[str, Any]:
    enriched = dict(block)
    enriched["_score"] = score
    enriched["_title_score"] = score
    enriched["_matched_exact_phrases"] = [
        phrase for phrase in relevant_exact_phrases(query) if phrase in (block.get("document_title") or "").lower()
    ]
    return enriched

def title_search(
    query: str,
    index: SearchIndex,
    limit: int,
    issuer: str | None = None,
    role: str | None = None,
    source: str | None = None,
    include_secondary: bool = True,
) -> list[dict[str, Any]]:
    representatives: dict[tuple[Any, Any, Any, Any], dict[str, Any]] = {}
    for block in index.blocks:
        if issuer and block.get("issuer") != issuer:
            continue
        if role and block.get("file_role") != role:
            continue
        if source and block.get("source") != source:
            continue
        if not include_secondary and block.get("file_role") in {"secondary_faq", "secondary_summary"}:
            continue
        title = block.get("document_title") or ""
        if not title:
            continue
        key = (block.get("canonical_id"), block.get("file_id"), block.get("file_role"), title)
        current = representatives.get(key)
        if current is None or document_representative_rank(block) < document_representative_rank(current):
            representatives[key] = block

    scored: list[tuple[float, dict[str, Any]]] = []
    for block in representatives.values():
        score = title_match_score(query, block.get("document_title") or "", index.stopwords)
        if score < TITLE_SEARCH_MIN_SCORE:
            continue
        scored.append((score, enrich_title_hit(block, score, query)))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored[:limit]]
