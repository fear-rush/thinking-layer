from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from ..common.text import normalize_space
from ..config.heuristics import heuristic_section
from ..retrieval.query_tools import load_query_lexicon, matched_items, tokenize_with_stopwords, unique_keep_order


ROLE_BOOST = heuristic_section("retrieval_ranking", "role_boost")


def query_terms_for(query: str, stopwords: set[str]) -> list[str]:
    expanded = query
    try:
        lexicon = load_query_lexicon()
    except SystemExit:
        lexicon = {}
    for item in matched_items(query, [*lexicon.get("entities", []), *lexicon.get("topics", [])]):
        matched_short_patterns = [
            pattern
            for pattern in item.get("matched_patterns") or []
            if re.fullmatch(r"\w+", pattern.lower()) and len(pattern) <= 5
        ]
        if matched_short_patterns:
            expansions = item.get("expansions") or []
            exact_phrases = item.get("exact_phrases") or []
            expanded += " " + " ".join([*expansions, *exact_phrases])
    return tokenize_with_stopwords(expanded, stopwords)


def relevant_exact_phrases(query: str) -> list[str]:
    lexicon = load_query_lexicon()
    phrases: list[str] = []
    for item in matched_items(query, [*lexicon.get("entities", []), *lexicon.get("topics", [])]):
        phrases.extend(item.get("exact_phrases") or [])
    return unique_keep_order([normalize_space(phrase).lower() for phrase in phrases if normalize_space(phrase)])


def candidate_terms_for(query_terms: list[str], doc_freq: dict[str, int] | Counter[str]) -> list[str]:
    config = heuristic_section("retrieval_ranking", "candidate_selection")
    sorted_terms = sorted(set(query_terms), key=lambda term: doc_freq.get(term, 10**9))
    return sorted_terms[: int(config.get("max_candidate_terms", 6))]


def bm25_term_score(
    query_counter: Counter[str],
    terms: dict[str, int] | Counter[str],
    doc_freq: dict[str, int] | Counter[str],
    total_docs: int,
    doc_len: int,
    avg_len: float,
) -> float:
    config = heuristic_section("retrieval_ranking", "bm25")
    k1 = float(config.get("k1", 1.4))
    b = float(config.get("b", 0.75))
    score = 0.0
    for term, qf in query_counter.items():
        tf = terms.get(term, 0)
        if not tf:
            continue
        df = doc_freq.get(term, 0)
        idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
        denom = tf + k1 * (1 - b + b * doc_len / (avg_len or 1))
        score += idf * (tf * (k1 + 1) / denom) * qf
    return score


def apply_exact_phrase_boost(score: float, query: str, title: str, text: str, phrases: list[str]) -> tuple[float, list[str]]:
    config = heuristic_section("retrieval_ranking", "lexical_score")
    query_l = query.lower()
    title_l = title.lower()
    text_l = text.lower()
    matched: list[str] = []
    for phrase in phrases:
        if phrase not in query_l:
            continue
        if phrase in title_l:
            score *= float(config.get("exact_phrase_title_multiplier", 1.45))
            matched.append(phrase)
        elif phrase in text_l:
            score *= float(config.get("exact_phrase_text_multiplier", 1.15))
            matched.append(phrase)
    return score, unique_keep_order(matched)


def apply_lexical_boosts(
    score: float,
    query: str,
    query_terms: list[str],
    stopwords: set[str],
    block: dict[str, Any],
    exact_phrases: list[str],
) -> tuple[float, list[str]]:
    config = heuristic_section("retrieval_ranking", "lexical_score")
    title = (block.get("document_title") or "").lower()
    text = (block.get("text") or "").lower()
    number = (block.get("number") or "").lower()
    haystack = " ".join([title, text, number])
    phrase_terms = [term for term in query_terms if len(term) >= int(config.get("phrase_term_min_chars", 3))]
    if query.lower() in haystack:
        score *= float(config.get("exact_query_multiplier", 1.35))
    elif len(phrase_terms) <= int(config.get("phrase_term_max_count_for_all_terms", 6)) and all(term in haystack for term in phrase_terms):
        score *= float(config.get("all_phrase_terms_multiplier", 1.15))

    title_token_set = set(tokenize_with_stopwords(title, stopwords))
    title_hits = len(set(query_terms) & title_token_set)
    if title_hits:
        score *= 1 + min(
            float(config.get("title_hit_max_boost", 0.50)),
            title_hits * float(config.get("title_hit_multiplier_per_hit", 0.08)),
        )

    score, matched_phrases = apply_exact_phrase_boost(score, query, title, text, exact_phrases)
    score *= ROLE_BOOST.get(block.get("file_role"), 1.0)
    if block.get("issuer") == "BI" and any(term in {"bi", "bank", "indonesia"} for term in query_terms):
        score *= float(config.get("issuer_match_multiplier", 1.08))
    if block.get("issuer") == "OJK" and "ojk" in query_terms:
        score *= float(config.get("issuer_match_multiplier", 1.08))
    return score, matched_phrases
