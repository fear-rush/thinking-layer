from __future__ import annotations

import argparse
import json
from typing import Any

from ..indexing.lexical import SearchIndex, get_search_index, snippet
from ..indexing.sqlite import sqlite_index_exists
from ..config.paths import REPORTS_DIR
from ..retrieval.planning import build_query_plan
from ..retrieval.search import execute_query_plan
from .retrieval import evaluate_results

NATURAL_LANGUAGE_EVALS = [
    {
        "query": "apa saja peraturan periklanan yang harus dipatuhi oleh bank?",
        "expected_titles": ["Penyediaan Informasi dan Penyampaian Informasi untuk Pemasaran Produk dan Layanan Jasa Keuangan"],
        "expected_issuers": ["OJK"]
    },
    {
        "query": "aturan apa yang mengatur iklan produk bank dan promosi ke nasabah?",
        "expected_titles": ["Penyediaan Informasi dan Penyampaian Informasi untuk Pemasaran Produk dan Layanan Jasa Keuangan"],
        "expected_issuers": ["OJK"]
    },
    {
        "query": "dokumen apa yang perlu disiapkan untuk pengembangan QRIS?",
        "expected_titles": ["Quick Response Code"],
        "expected_issuers": ["BI"]
    },
    {
        "query": "apa kewajiban bank terkait pelaporan SLIK?",
        "expected_titles": ["Pelaporan dan Permintaan Informasi Debitur", "Sistem Layanan Informasi Keuangan"],
        "expected_issuers": ["OJK"]
    },
    {
        "query": "sanksi apa kalau bank terlambat menyampaikan laporan ke OJK?",
        "expected_title_groups": [["Transparansi", "Publikasi", "Laporan Bank"], ["Sanksi Administratif"]],
        "expected_issuers": ["OJK"]
    },
    {
        "query": "peraturan BI tentang penyedia jasa pembayaran apa saja?",
        "expected_titles": ["Penyedia Jasa Pembayaran"],
        "expected_issuers": ["BI"]
    },
    {
        "query": "aturan OJK tentang perlindungan data pribadi nasabah",
        "expected_title_groups": [["Informasi Pribadi", "Konsumen"]],
        "expected_issuers": ["OJK"]
    },
    {
        "query": "apa dasar hukum manajemen risiko teknologi informasi bank?",
        "expected_title_groups": [["Manajemen Risiko", "Teknologi Informasi", "Bank Umum"]],
        "expected_issuers": ["OJK"]
    },
    {
        "query": "peraturan yang mengatur anti pencucian uang dan pendanaan terorisme untuk bank",
        "expected_title_groups": [["Anti Pencucian Uang", "Pencegahan Pendanaan Terorisme"]],
        "expected_issuers": ["OJK"]
    },
    {
        "query": "apa perbedaan aturan BI dan OJK tentang sistem pembayaran?",
        "expected_titles": ["Sistem Pembayaran"],
        "expected_issuers": ["BI", "OJK"]
    },
    {
        "query": "aturan layanan digital bank umum",
        "expected_titles": ["Layanan Digital oleh Bank Umum"],
        "expected_issuers": ["OJK"]
    },
    {
        "query": "regulasi tata kelola bank syariah",
        "expected_title_groups": [["Tata Kelola", "Syariah"]],
        "expected_issuers": ["OJK"]
    },
    {
        "query": "apa syarat fit and proper test direksi bank?",
        "expected_titles": ["Penilaian Kemampuan dan Kepatutan"],
        "expected_issuers": ["OJK"]
    },
    {
        "query": "aturan rencana bisnis bank umum",
        "expected_titles": ["Rencana Bisnis Bank Umum"],
        "expected_issuers": ["OJK"]
    },
    {
        "query": "peraturan terbaru tentang aset kripto di OJK",
        "expected_titles": ["Aset Keuangan Digital", "Aset Kripto"],
        "expected_issuers": ["OJK"]
    }
]

def cmd_eval_natural(args: argparse.Namespace) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    lines = ["# Natural Language Query Evaluation", ""]
    rows = []
    evaluations = []
    index_cache: dict[tuple[Any, Any, Any, bool], SearchIndex] = {}
    base_index = None if sqlite_index_exists() else get_search_index(prefer_persisted=True)
    for spec in NATURAL_LANGUAGE_EVALS:
        plan = build_query_plan(spec["query"], max_searches=args.max_searches)
        results = execute_query_plan(plan, args.limit, index_cache=index_cache, base_index=base_index)
        evaluation = evaluate_results(spec, results)
        evaluations.append(evaluation)
        rows.append({"query": spec["query"], "plan": plan, "evaluation": evaluation, "results": [
            {
                "score": row.get("_score"),
                "source": row.get("source"),
                "issuer": row.get("issuer"),
                "file_role": row.get("file_role"),
                "document_title": row.get("document_title"),
                "page": row.get("page_start"),
                "pasal": row.get("pasal"),
                "ayat": row.get("ayat"),
                "planned_query": row.get("_planned_query"),
                "plan_reason": row.get("_plan_reason"),
                "snippet": snippet(row.get("text") or "", spec["query"])
            } for row in results
        ]})
        lines.extend([
            f"## {spec['query']}",
            "",
            f"- Score: `{evaluation['score']}`",
            f"- Accepted: `{evaluation['accepted']}`",
            f"- Intents: `{plan['intents']}`",
            f"- Topics: `{plan['topics']}`",
            f"- Entities: `{plan['entities']}`",
            f"- Title hits: `{evaluation['title_hits']}`",
            f"- Title group hits: `{evaluation['title_group_hits']}`",
            f"- Issuer hits: `{evaluation['issuer_hits']}`",
            "",
        ])
        for idx, row in enumerate(results[:5], start=1):
            lines.append(f"{idx}. `{row.get('issuer')}` `{row.get('file_role')}` p`{row.get('page_start')}` `{row.get('pasal') or '-'}` - {row.get('document_title')}")
        lines.append("")

    accepted = sum(1 for item in evaluations if item["accepted"])
    avg = sum(item["score"] for item in evaluations) / max(1, len(evaluations))
    lines = [
        "# Natural Language Query Evaluation Summary",
        "",
        f"- Queries: {len(evaluations)}",
        f"- Accepted: {accepted}/{len(evaluations)}",
        f"- Average score: {avg:.3f}",
        "",
    ] + lines
    (REPORTS_DIR / "natural_language_eval.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPORTS_DIR / "natural_language_eval.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote reports/natural_language_eval.md")
    print("Wrote reports/natural_language_eval.json")
