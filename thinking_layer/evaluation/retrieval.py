from __future__ import annotations

import argparse
import json
from typing import Any

from ..config.heuristics import heuristic_section
from ..indexing.lexical import format_search_results, get_search_index, snippet
from ..indexing.sqlite import sqlite_doc_count, sqlite_index_is_current
from ..config.paths import REPORTS_DIR
from ..retrieval.planning import build_query_plan
from ..retrieval.search import execute_query_plan

SMOKE_QUERIES = [
    {
        "query": "aturan terkait penyedia jasa pembayaran dari BI dan OJK",
        "expected_titles": ["Penyedia Jasa Pembayaran"],
        "expected_issuers": ["BI", "OJK"],
    },
    {
        "query": "komparasi peraturan OJK dan BI terkait penyedia jasa pembayaran",
        "expected_titles": ["Penyedia Jasa Pembayaran"],
        "expected_issuers": ["BI", "OJK"],
    },
    {
        "query": "SNAP Standar Nasional Open API Pembayaran",
        "expected_titles": ["Standar Nasional Open Application Programming Interface Pembayaran"],
        "expected_issuers": ["BI"],
    },
    {
        "query": "QRIS pengembangan aktivitas produk kerja sama",
        "expected_titles": ["Quick Response Code"],
        "expected_issuers": ["BI"],
    },
    {
        "query": "pelaporan bank umum melalui sistem pelaporan OJK",
        "expected_title_groups": [["Pelaporan", "Bank Umum", "Sistem Pelaporan Otoritas Jasa Keuangan"]],
        "expected_issuers": ["OJK"],
    },
    {
        "query": "SLIK pelaporan permintaan informasi debitur",
        "expected_titles": ["Pelaporan dan Permintaan Informasi Debitur", "Sistem Layanan Informasi Keuangan"],
        "expected_issuers": ["OJK"],
    },
    {
        "query": "APU PPT pencegahan pendanaan terorisme",
        "expected_titles": ["Anti Pencucian Uang", "Pencegahan Pendanaan Terorisme"],
        "expected_issuers": ["OJK"],
    },
    {
        "query": "layanan keuangan digital bank umum",
        "expected_titles": ["Layanan Digital oleh Bank Umum", "Layanan Perbankan Digital"],
        "expected_issuers": ["OJK"],
    },
    {
        "query": "manajemen risiko teknologi informasi bank umum",
        "expected_titles": ["Manajemen Risiko", "Teknologi Informasi", "Bank Umum"],
        "expected_issuers": ["OJK"],
    },
    {
        "query": "transparansi publikasi laporan bank umum",
        "expected_titles": ["Transparansi", "Publikasi Laporan", "Bank Umum"],
        "expected_issuers": ["OJK"],
    },
]

def evaluate_results(spec: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    config = heuristic_section("evaluation_rubrics", "retrieval")
    top_titles = [row.get("document_title") or "" for row in results[: int(config.get("top_title_count", 5))]]
    top_issuers = {row.get("issuer") for row in results[: int(config.get("top_issuer_count", 8))]}
    expected_titles = spec.get("expected_titles") or []
    expected_title_groups = spec.get("expected_title_groups") or []
    expected_issuers = spec.get("expected_issuers") or []
    title_hits = [
        expected
        for expected in expected_titles
        if any(expected.lower() in title.lower() for title in top_titles)
    ]
    title_group_hits = [
        group
        for group in expected_title_groups
        if any(all(expected.lower() in title.lower() for expected in group) for title in top_titles)
    ]
    if expected_title_groups:
        title_score = len(title_group_hits) / max(1, len(expected_title_groups))
    else:
        title_score = len(title_hits) / max(1, len(expected_titles))
    issuer_hits = [issuer for issuer in expected_issuers if issuer in top_issuers]
    top_citation_count = int(config.get("top_citation_count", 5))
    page_citation_rate = sum(1 for row in results[:top_citation_count] if row.get("page_start")) / max(1, min(top_citation_count, len(results)))
    primary_rate = sum(1 for row in results[:top_citation_count] if row.get("file_role") == "primary_regulation") / max(1, min(top_citation_count, len(results)))
    weights = config.get("weights") or {}
    score = 0.0
    score += float(weights.get("title_score", 0.45)) * title_score
    score += float(weights.get("issuer_score", 0.30)) * (len(issuer_hits) / max(1, len(expected_issuers)))
    score += float(weights.get("page_citation_rate", 0.15)) * page_citation_rate
    score += float(weights.get("primary_rate", 0.10)) * primary_rate
    return {
        "score": round(score, 3),
        "accepted": score >= float(config.get("accepted_threshold", 0.82)),
        "title_hits": title_hits,
        "title_group_hits": title_group_hits,
        "issuer_hits": issuer_hits,
        "page_citation_rate": round(page_citation_rate, 3),
        "primary_rate": round(primary_rate, 3),
    }

def cmd_smoke_test(args: argparse.Namespace) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    index = None if sqlite_index_is_current() else get_search_index(prefer_persisted=True)
    indexed_blocks = sqlite_doc_count() if sqlite_index_is_current() else len(index.blocks)
    lines = [
        "# Retrieval Smoke Test",
        "",
        f"Indexed blocks: {indexed_blocks}",
        f"Queries: {len(SMOKE_QUERIES)}",
        "",
    ]
    json_rows: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    for spec in SMOKE_QUERIES:
        query = spec["query"]
        plan = build_query_plan(query, max_searches=args.max_searches)
        results = execute_query_plan(plan, args.limit, base_index=index)
        evaluation = evaluate_results(spec, results)
        evaluations.append(evaluation)
        lines.extend(
            [
                f"## Evaluation: {query}",
                "",
                f"- Score: `{evaluation['score']}`",
                f"- Accepted: `{evaluation['accepted']}`",
                f"- Title hits: `{evaluation['title_hits']}`",
                f"- Issuer hits: `{evaluation['issuer_hits']}`",
                f"- Page citation rate: `{evaluation['page_citation_rate']}`",
                f"- Primary rate: `{evaluation['primary_rate']}`",
                "",
            ]
        )
        lines.extend(format_search_results(query, results).splitlines())
        lines.append("")
        json_rows.append(
            {
                "query": query,
                "plan": plan,
                "evaluation": evaluation,
                "results": [
                    {
                        "score": row.get("_score"),
                        "source": row.get("source"),
                        "issuer": row.get("issuer"),
                        "file_role": row.get("file_role"),
                        "document_title": row.get("document_title"),
                        "page": row.get("page_start"),
                        "pasal": row.get("pasal"),
                        "ayat": row.get("ayat"),
                        "block_type": row.get("block_type"),
                        "snippet": snippet(row.get("text") or "", query),
                    }
                    for row in results
                ],
            }
        )

    accepted_count = sum(1 for item in evaluations if item["accepted"])
    average_score = sum(item["score"] for item in evaluations) / max(1, len(evaluations))
    summary = [
        "# Retrieval Evaluation Summary",
        "",
        f"- Queries: {len(evaluations)}",
        f"- Accepted: {accepted_count}/{len(evaluations)}",
        f"- Average score: {average_score:.3f}",
        f"- Pass threshold: query score >= 0.82",
        "",
    ]
    for spec, evaluation in zip(SMOKE_QUERIES, evaluations):
        summary.append(f"- `{spec['query']}`: score `{evaluation['score']}`, accepted `{evaluation['accepted']}`")
    lines = summary + [""] + lines

    (REPORTS_DIR / "retrieval_smoke_test.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPORTS_DIR / "retrieval_smoke_test.json").write_text(
        json.dumps(json_rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Wrote reports/retrieval_smoke_test.md")
    print("Wrote reports/retrieval_smoke_test.json")
