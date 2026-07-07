from __future__ import annotations

import argparse
from typing import Any

from ..config.heuristics import heuristic_section
from ..common.text import normalize_space
from .query_tools import contains_pattern, load_query_lexicon, matched_items, query_overlap_score, unique_keep_order

def ordered_expansions(query: str, item: dict[str, Any]) -> list[str]:
    expansions = item.get("expansions") or []
    return sorted(expansions, key=lambda value: query_overlap_score(query, value), reverse=True)

def ordered_matches(query: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def priority(item: dict[str, Any]) -> tuple[float, int]:
        matched = " ".join(item.get("matched_patterns") or [])
        expansions = " ".join(item.get("expansions") or [])
        return (
            query_overlap_score(query, matched) + query_overlap_score(query, expansions) * 0.15,
            max((len(pattern) for pattern in item.get("matched_patterns") or []), default=0),
        )

    return sorted(items, key=priority, reverse=True)

def should_expand_entity(entity: dict[str, Any], has_topic_matches: bool) -> bool:
    config = heuristic_section("retrieval_ranking", "query_planning")
    name = entity.get("name")
    if has_topic_matches and name in set(config.get("generic_bank_entity_names") or []):
        return False
    if name == config.get("bank_entity_name", "bank"):
        matched = {pattern.lower() for pattern in entity.get("matched_patterns") or []}
        return bool(matched - set(config.get("bank_entity_generic_patterns") or ["bank"]))
    return True

def infer_issuers(query: str, topic_matches: list[dict[str, Any]], issuer_matches: list[dict[str, Any]]) -> list[str | None]:
    config = heuristic_section("retrieval_ranking", "query_planning")
    issuers = [item["issuer"] for item in issuer_matches if item.get("issuer")]
    issuers.extend(item["issuer"] for item in topic_matches if item.get("issuer"))
    issuer_patterns = config.get("issuer_patterns") or {}
    if any(contains_pattern(query, pattern) for pattern in issuer_patterns.get("OJK", ["ojk"])) and "BI" not in issuers:
        issuers.append("OJK")
    if any(contains_pattern(query, pattern) for pattern in issuer_patterns.get("BI", ["bi", "bank indonesia"])) and "BI" not in issuers:
        issuers.append("BI")
    if contains_pattern(query, "bank") and not issuers:
        issuers.append(str(config.get("bank_default_issuer", "OJK")))
    if not issuers:
        issuers.append(None)
    return unique_keep_order(issuers)

def build_query_plan(query: str, max_searches: int = 12) -> dict[str, Any]:
    planning_config = heuristic_section("retrieval_ranking", "query_planning")
    lexicon = load_query_lexicon()
    intent_matches = matched_items(query, lexicon.get("intents", []))
    issuer_matches = matched_items(query, lexicon.get("issuers", []))
    entity_matches = ordered_matches(query, matched_items(query, lexicon.get("entities", [])))
    topic_matches = ordered_matches(query, matched_items(query, lexicon.get("topics", [])))

    intents = [item["intent"] for item in intent_matches] or [str(planning_config.get("default_intent", "find_regulations"))]
    issuers = infer_issuers(query, topic_matches, issuer_matches)
    explicit_issuers = unique_keep_order([item["issuer"] for item in issuer_matches if item.get("issuer")])
    if explicit_issuers:
        issuers = explicit_issuers
    else:
        entity_issuers = unique_keep_order([item["issuer"] for item in entity_matches if item.get("issuer")])
        if entity_issuers:
            issuers = entity_issuers
    entity_terms: list[str] = []
    topic_terms: list[str] = []
    for item in entity_matches:
        if not should_expand_entity(item, bool(topic_matches)):
            continue
        entity_terms.extend(item.get("expansions") or [])
    for item in topic_matches:
        topic_terms.extend(item.get("expansions") or [])

    base_terms = unique_keep_order([query, *topic_terms, *entity_terms])
    searches: list[dict[str, Any]] = []

    # Raw query remains useful, but it should not be the only search.
    searches.append(
        {
            "query": query,
            "issuer": explicit_issuers[0] if len(explicit_issuers) == 1 else (None if len([i for i in issuers if i]) > 1 else issuers[0]),
            "role": None,
            "include_secondary": True,
            "reason": "raw_user_query",
        }
    )

    generic_bank_names = set(planning_config.get("generic_bank_entity_names") or ["bank"])
    for entity in [item for item in entity_matches if item.get("name") not in generic_bank_names]:
        if not should_expand_entity(entity, bool(topic_matches)):
            continue
        for expansion in ordered_expansions(query, entity):
            for issuer in issuers:
                searches.append(
                    {
                        "query": expansion,
                        "issuer": issuer,
                        "role": "primary_regulation",
                        "include_secondary": True,
                        "reason": f"entity:{entity['name']}",
                    }
                )

    topic_searches: list[dict[str, Any]] = []
    for topic in topic_matches:
        topic_issuer = topic.get("issuer")
        if explicit_issuers:
            topic_issuers = explicit_issuers
        elif topic_issuer:
            topic_issuers = [topic_issuer]
        else:
            topic_issuers = issuers
        for expansion in ordered_expansions(query, topic):
            for issuer in topic_issuers:
                topic_searches.append(
                    {
                        "query": normalize_space(expansion),
                        "issuer": issuer,
                        "role": "primary_regulation",
                        "include_secondary": True,
                        "reason": f"topic:{topic['name']}",
                    }
                )

    topic_searches.sort(key=lambda search: query_overlap_score(query, search["query"]), reverse=True)
    searches.extend(topic_searches)

    if not topic_matches and not [item for item in entity_matches if item.get("name") not in generic_bank_names]:
        for entity in entity_matches:
            if not should_expand_entity(entity, bool(topic_matches)):
                continue
            for expansion in entity.get("expansions") or []:
                for issuer in issuers:
                    searches.append(
                        {
                            "query": expansion,
                            "issuer": issuer,
                            "role": "primary_regulation",
                            "include_secondary": True,
                            "reason": f"entity:{entity['name']}",
                        }
                    )

    # Intent-specific broadening.
    intent_expansions = planning_config.get("intent_expansions") or {}
    for intent in intents:
        expansion_config = intent_expansions.get(intent)
        if not expansion_config:
            continue
        for term in expansion_config.get("queries") or []:
            searches.append(
                {
                    "query": term,
                    "issuer": issuers[0],
                    "role": expansion_config.get("role"),
                    "include_secondary": bool(expansion_config.get("include_secondary", True)),
                    "reason": f"intent:{intent}",
                }
            )

    if len(searches) == 1:
        for term in base_terms[1:]:
            searches.append({"query": term, "issuer": issuers[0], "role": None, "include_secondary": True, "reason": "lexical_expansion"})

    searches = unique_keep_order(searches)
    return {
        "raw_query": query,
        "intents": intents,
        "issuers": issuers,
        "entities": [item["name"] for item in entity_matches],
        "topics": [item["name"] for item in topic_matches],
        "searches": searches[:max_searches],
    }

def format_query_plan(plan: dict[str, Any]) -> str:
    lines = [
        "# Query Plan",
        "",
        f"- Raw query: `{plan['raw_query']}`",
        f"- Intents: `{plan['intents']}`",
        f"- Issuers: `{plan['issuers']}`",
        f"- Entities: `{plan['entities']}`",
        f"- Topics: `{plan['topics']}`",
        "",
        "## Searches",
        "",
    ]
    for index, search in enumerate(plan["searches"], start=1):
        lines.append(
            f"{index}. `{search['query']}` | issuer `{search.get('issuer')}` | role `{search.get('role')}` | reason `{search['reason']}`"
        )
    return "\n".join(lines) + "\n"

def cmd_plan_query(args: argparse.Namespace) -> None:
    plan = build_query_plan(args.query, max_searches=args.max_searches)
    print(format_query_plan(plan))
