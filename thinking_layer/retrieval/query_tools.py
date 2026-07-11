from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from ..common.io import read_json
from ..config.paths import QUERY_LEXICON_PATH, ROOT, STOPWORDS_PATH

@lru_cache(maxsize=1)
def load_stopwords() -> set[str]:
    if not STOPWORDS_PATH.exists():
        raise SystemExit(
            f"Missing {STOPWORDS_PATH.relative_to(ROOT)}. "
            "Download it from https://raw.githubusercontent.com/stopwords-iso/stopwords-id/refs/heads/master/raw/indonesian-stopwords-complete.txt"
        )
    with STOPWORDS_PATH.open("r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip() and not line.startswith("#")}

def tokenize(value: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+(?:/[a-zA-Z0-9.]+)*", value.lower())
    stopwords = load_stopwords()
    return [token for token in tokens if len(token) > 1 and token not in stopwords]

def tokenize_with_stopwords(value: str, stopwords: set[str]) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+(?:/[a-zA-Z0-9.]+)*", value.lower())
    return [token for token in tokens if len(token) > 1 and token not in stopwords]

@lru_cache(maxsize=1)
def load_query_lexicon() -> dict[str, Any]:
    if not QUERY_LEXICON_PATH.exists():
        raise SystemExit(f"Missing {QUERY_LEXICON_PATH.relative_to(ROOT)}")
    return read_json(QUERY_LEXICON_PATH)

def contains_pattern(query: str, pattern: str) -> bool:
    lowered_query = query.lower()
    lowered_pattern = pattern.lower()
    if not lowered_pattern:
        return False
    if re.fullmatch(r"\w+", lowered_pattern) and len(lowered_pattern) <= 3:
        return bool(re.search(rf"(?<!\w){re.escape(lowered_pattern)}(?!\w)", lowered_query))
    return lowered_pattern in lowered_query

def matched_items(query: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches = []
    for item in items:
        patterns = item.get("patterns") or []
        if any(contains_pattern(query, pattern) for pattern in item.get("exclude_patterns") or []):
            continue
        hit_patterns = [pattern for pattern in patterns if contains_pattern(query, pattern)]
        if hit_patterns:
            enriched = dict(item)
            enriched["matched_patterns"] = hit_patterns
            matches.append(enriched)
    return matches

def unique_keep_order(values: list[Any]) -> list[Any]:
    seen = set()
    out = []
    for value in values:
        marker = json.dumps(value, sort_keys=True, ensure_ascii=False) if isinstance(value, (dict, list)) else value
        if marker in seen:
            continue
        seen.add(marker)
        out.append(value)
    return out

def query_overlap_score(query: str, value: str) -> float:
    stopwords = load_stopwords()
    query_tokens = set(tokenize_with_stopwords(query, stopwords))
    value_tokens = tokenize_with_stopwords(value, stopwords)
    if not query_tokens or not value_tokens:
        return 0.0
    overlap = len(query_tokens & set(value_tokens))
    return overlap + min(0.5, len(value_tokens) * 0.03)
