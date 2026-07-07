from __future__ import annotations

import argparse
import sqlite3
from typing import Any

from ..config.heuristics import heuristic_section
from ..indexing.lexical import SearchIndex, bm25_search, dedupe_results, filter_index, format_search_results, get_search_index, needs_balanced_issuer_search, planned_search
from ..indexing.sqlite import sqlite_index_exists, sqlite_metadata, sqlite_search, sqlite_title_search
from ..indexing.title import title_search
from ..config.paths import SEARCH_INDEX_DB
from .planning import build_query_plan, format_query_plan
from .query_tools import query_overlap_score

def cmd_search(args: argparse.Namespace) -> None:
    if sqlite_index_exists():
        results = sqlite_search(
            args.query,
            args.limit,
            issuer=args.issuer,
            role=args.role,
            source=args.source,
            include_secondary=args.include_secondary,
        )
    else:
        base_index = get_search_index(prefer_persisted=True)
        index = filter_index(base_index, args.issuer, args.role, args.source, args.include_secondary)
        results = bm25_search(args.query, index, args.limit, issuer=args.issuer) if args.issuer else planned_search(args.query, index, args.limit)
    output = format_search_results(args.query, results)
    print(output)

def execute_query_plan(
    plan: dict[str, Any],
    limit: int,
    index_cache: dict[tuple[Any, Any, Any, bool], SearchIndex] | None = None,
    base_index: SearchIndex | None = None,
) -> list[dict[str, Any]]:
    all_results: list[dict[str, Any]] = []
    if sqlite_index_exists():
        conn = sqlite3.connect(SEARCH_INDEX_DB)
        conn.row_factory = sqlite3.Row
        metadata = sqlite_metadata(conn)
        try:
            for search_rank, search in enumerate(plan["searches"], start=1):
                title_results = sqlite_title_search(
                    search["query"],
                    max(4, min(limit, 8)),
                    issuer=search.get("issuer"),
                    role=search.get("role"),
                    source=None,
                    include_secondary=bool(search.get("include_secondary", True)),
                    conn=conn,
                )
                for result_rank, row in enumerate(title_results, start=1):
                    enriched = dict(row)
                    enriched["_planned_query"] = search["query"]
                    enriched["_plan_reason"] = f"title:{search['reason']}"
                    enriched["_bm25_score"] = row.get("_score", 0)
                    enriched["_score"] = planned_result_score(plan["raw_query"], {**search, "reason": enriched["_plan_reason"]}, search_rank, result_rank, row)
                    all_results.append(enriched)
                results = sqlite_search(
                    search["query"],
                    max(limit, 8),
                    issuer=search.get("issuer"),
                    role=search.get("role"),
                    source=None,
                    include_secondary=bool(search.get("include_secondary", True)),
                    conn=conn,
                    metadata=metadata,
                )
                for result_rank, row in enumerate(results, start=1):
                    enriched = dict(row)
                    enriched["_planned_query"] = search["query"]
                    enriched["_plan_reason"] = search["reason"]
                    enriched["_bm25_score"] = row.get("_score", 0)
                    enriched["_score"] = planned_result_score(plan["raw_query"], search, search_rank, result_rank, row)
                    all_results.append(enriched)
        finally:
            conn.close()
        all_results.sort(key=lambda row: row.get("_score", 0), reverse=True)
        return dedupe_results(all_results, limit)

    if index_cache is None:
        index_cache = {}
    if base_index is None:
        base_index = get_search_index(prefer_persisted=True)
    for search_rank, search in enumerate(plan["searches"], start=1):
        key = (search.get("issuer"), search.get("role"), None, bool(search.get("include_secondary", True)))
        if key not in index_cache:
            index_cache[key] = filter_index(
                base_index,
                issuer=search.get("issuer"),
                role=search.get("role"),
                source=None,
                include_secondary=bool(search.get("include_secondary", True)),
            )
        index = index_cache[key]
        title_results = title_search(
            search["query"],
            index,
            max(4, min(limit, 8)),
            issuer=search.get("issuer"),
            role=search.get("role"),
            source=None,
            include_secondary=bool(search.get("include_secondary", True)),
        )
        for result_rank, row in enumerate(title_results, start=1):
            enriched = dict(row)
            enriched["_planned_query"] = search["query"]
            enriched["_plan_reason"] = f"title:{search['reason']}"
            enriched["_bm25_score"] = row.get("_score", 0)
            enriched["_score"] = planned_result_score(plan["raw_query"], {**search, "reason": enriched["_plan_reason"]}, search_rank, result_rank, row)
            all_results.append(enriched)
        results = bm25_search(search["query"], index, max(limit, 8), issuer=search.get("issuer"))
        for result_rank, row in enumerate(results, start=1):
            enriched = dict(row)
            enriched["_planned_query"] = search["query"]
            enriched["_plan_reason"] = search["reason"]
            enriched["_bm25_score"] = row.get("_score", 0)
            enriched["_score"] = planned_result_score(plan["raw_query"], search, search_rank, result_rank, row)
            all_results.append(enriched)

    all_results.sort(key=lambda row: row.get("_score", 0), reverse=True)
    return dedupe_results(all_results, limit)

def plan_reason_boost(reason: str) -> float:
    config = heuristic_section("retrieval_ranking", "planned_result").get("reason_boost") or {}
    if reason.startswith("title:"):
        return float(config.get("title", 1.40))
    if reason.startswith("topic:"):
        return float(config.get("topic", 1.25))
    if reason.startswith("intent:"):
        return float(config.get("intent", 1.08))
    if reason.startswith("entity:"):
        return float(config.get("entity", 1.03))
    return float(config.get("default", 0.90))

def sector_alignment_factor(raw_query: str, title: str) -> float:
    config = heuristic_section("retrieval_ranking", "sector_alignment")
    query_l = raw_query.lower()
    title_l = title.lower()
    bank_umum_query = any(term in query_l for term in config.get("bank_umum_query_terms") or [])
    bpr_query = any(term in query_l for term in config.get("bpr_query_terms") or [])
    bank_umum_title = any(term in title_l for term in config.get("bank_umum_title_terms") or [])
    bpr_title = any(term in title_l for term in config.get("bpr_title_terms") or [])
    if bank_umum_query and bpr_title and not bank_umum_title:
        return float(config.get("bank_umum_query_bpr_title_multiplier", 0.55))
    if bpr_query and bank_umum_title and not bpr_title:
        return float(config.get("bpr_query_bank_umum_title_multiplier", 0.70))
    return 1.0

def planned_result_score(raw_query: str, search: dict[str, Any], search_rank: int, result_rank: int, row: dict[str, Any]) -> float:
    config = heuristic_section("retrieval_ranking", "planned_result")
    title = row.get("document_title") or ""
    title_overlap = query_overlap_score(raw_query, title)
    search_overlap = query_overlap_score(raw_query, search.get("query") or "")
    rank_score = float(config.get("rank_score_base", 100.0)) / (result_rank + int(config.get("rank_score_offset", 5)))
    search_order_decay = 1.0 / (1.0 + max(0, search_rank - 1) * float(config.get("search_order_decay", 0.10)))
    overlap_boost = 1.0 + min(
        float(config.get("overlap_max_boost", 0.60)),
        title_overlap * float(config.get("title_overlap_weight", 0.10)) + search_overlap * float(config.get("search_overlap_weight", 0.04)),
    )
    title_quality = 1.0
    if search["reason"].startswith("title:"):
        title_quality = float(config.get("title_quality_base", 0.70)) + min(
            float(config.get("title_quality_max_bonus", 0.70)),
            float(row.get("_title_score") or 0.0) / float(config.get("title_quality_score_divisor", 160.0)),
        )
    return (
        rank_score
        * plan_reason_boost(search["reason"])
        * search_order_decay
        * overlap_boost
        * title_quality
        * sector_alignment_factor(raw_query, title)
    )

def cmd_planned_search(args: argparse.Namespace) -> None:
    plan = build_query_plan(args.query, max_searches=args.max_searches)
    base_index = None if sqlite_index_exists() else get_search_index(prefer_persisted=True)
    results = execute_query_plan(plan, args.limit, base_index=base_index)
    lines = [format_query_plan(plan), "", format_search_results(args.query, results)]
    print("\n".join(lines))
