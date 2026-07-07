from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..common.io import iter_ndjson_file
from ..common.text import normalize_space
from ..config.heuristics import load_heuristic_config
from ..config.paths import REPORTS_DIR, ROOT, SOURCE_CORPUS_PATH
from .quality import extraction_issue_flags


def extraction_spot_check_config() -> dict[str, Any]:
    return load_heuristic_config("extraction_spot_check")


def title_matches(title: str, patterns: list[str]) -> bool:
    title_l = title.lower()
    return any(pattern.lower() in title_l for pattern in patterns)


def row_issue_flags(row: dict[str, Any]) -> list[str]:
    return extraction_issue_flags(row)


def summarize_rows(rows: list[dict[str, Any]], thresholds: dict[str, Any], max_documents: int) -> dict[str, Any]:
    section_types = Counter(str(row.get("section_type")) for row in rows)
    citation_quality = Counter(str(row.get("citation_quality")) for row in rows)
    documents = Counter(str(row.get("document_title")) for row in rows)
    pages = {row.get("page_start") for row in rows if row.get("page_start")}
    page_rate = sum(1 for row in rows if row.get("page_start")) / max(1, len(rows))
    table_rate = section_types.get("table", 0) / max(1, len(rows))
    doc_page_only_rate = citation_quality.get("document_page", 0) / max(1, len(rows))
    article_or_ayat_rate = sum(1 for row in rows if row.get("pasal") or row.get("ayat")) / max(1, len(rows))
    issue_counts: Counter[str] = Counter()
    for row in rows:
        issue_counts.update(row_issue_flags(row))

    warnings = []
    if page_rate < float(thresholds.get("min_page_rate", 0.98)):
        warnings.append("low_page_coverage")
    if table_rate > float(thresholds.get("max_table_rate", 0.45)):
        warnings.append("high_table_rate")
    if doc_page_only_rate > float(thresholds.get("max_document_page_only_rate", 0.35)):
        warnings.append("high_document_page_only_rate")
    if article_or_ayat_rate < float(thresholds.get("min_article_or_ayat_rate", 0.35)):
        warnings.append("low_pasal_ayat_rate")
    warnings.extend(issue for issue, count in issue_counts.items() if count)

    return {
        "rows": len(rows),
        "documents": dict(documents.most_common(max_documents)),
        "document_count": len(documents),
        "page_count": len(pages),
        "section_types": dict(section_types.most_common()),
        "citation_quality": dict(citation_quality.most_common()),
        "page_rate": round(page_rate, 3),
        "table_rate": round(table_rate, 3),
        "document_page_only_rate": round(doc_page_only_rate, 3),
        "article_or_ayat_rate": round(article_or_ayat_rate, 3),
        "issue_counts": dict(issue_counts.most_common()),
        "warnings": sorted(set(warnings)),
    }


def representative_examples(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    examples = []
    preferred_sections = ["ayat", "pasal", "table", "paragraph", "attachment"]
    used_ids: set[str] = set()
    for section in preferred_sections:
        for row in rows:
            row_id = str(row.get("block_id"))
            if row_id in used_ids or row.get("section_type") != section:
                continue
            used_ids.add(row_id)
            examples.append(example_payload(row))
            break
        if len(examples) >= limit:
            return examples
    for row in rows:
        row_id = str(row.get("block_id"))
        if row_id in used_ids:
            continue
        used_ids.add(row_id)
        examples.append(example_payload(row))
        if len(examples) >= limit:
            break
    return examples


def example_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "document": row.get("document_title"),
        "issuer": row.get("issuer"),
        "file_role": row.get("file_role"),
        "section_type": row.get("section_type"),
        "citation_quality": row.get("citation_quality"),
        "citation": (row.get("citation") or {}).get("text"),
        "flags": row_issue_flags(row),
        "text": normalize_space(str(row.get("text") or ""))[:360],
    }


def evidence_probe(query: str, max_citations: int) -> dict[str, Any]:
    from ..retrieval.evidence import build_evidence_pack

    pack = build_evidence_pack(query, max_searches=6, limit=10, per_document_limit=2)
    citations = []
    for doc in pack.get("documents") or []:
        for item in doc.get("citations") or []:
            citations.append(
                {
                    "issuer": item.get("issuer"),
                    "document": (item.get("citation") or {}).get("document"),
                    "citation": (item.get("citation") or {}).get("text"),
                    "citation_quality": item.get("citation_quality"),
                    "section_type": item.get("section_type"),
                    "snippet": item.get("snippet"),
                }
            )
            if len(citations) >= max_citations:
                break
        if len(citations) >= max_citations:
            break
    return {
        "query": query,
        "confidence": pack.get("confidence"),
        "topic_coverage": pack.get("topic_coverage"),
        "top_citations": citations,
    }


def build_extraction_spot_check(source_path: Path = SOURCE_CORPUS_PATH) -> dict[str, Any]:
    config = extraction_spot_check_config()
    thresholds = config.get("thresholds") or {}
    audit_config = config.get("audit") or {}
    max_examples = int(audit_config.get("max_examples_per_target", 6))
    max_citations = int(audit_config.get("max_evidence_citations", 4))
    max_documents = int(audit_config.get("max_documents_per_target", 10))

    rows_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    targets = config.get("targets") or []
    for row in iter_ndjson_file(source_path):
        title = str(row.get("document_title") or "")
        issuer = row.get("issuer")
        for target in targets:
            if target.get("issuer") and issuer != target.get("issuer"):
                continue
            if title_matches(title, target.get("title_patterns") or []):
                rows_by_target[target["name"]].append(row)

    target_reports = []
    for target in targets:
        rows = rows_by_target.get(target["name"], [])
        target_reports.append(
            {
                "name": target["name"],
                "issuer": target.get("issuer"),
                "title_patterns": target.get("title_patterns"),
                "summary": summarize_rows(rows, thresholds, max_documents),
                "examples": representative_examples(rows, max_examples),
                "evidence_probe": evidence_probe(str(target.get("query") or target["name"]), max_citations),
            }
        )

    return {
        "source_path": str(source_path.relative_to(ROOT) if source_path.is_relative_to(ROOT) else source_path),
        "targets": target_reports,
    }


def write_extraction_spot_check(report: dict[str, Any], md_path: Path, json_path: Path) -> None:
    lines = [
        "# Extraction Spot Check",
        "",
        "Focused review of high-value regulation areas using the current citation-ready source corpus.",
        "",
        f"- Source: `{report['source_path']}`",
        "",
        "## Summary",
        "",
        "| Target | Rows | Documents | Page rate | Pasal/Ayat rate | Table rate | Warnings |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for target in report["targets"]:
        summary = target["summary"]
        warnings = ", ".join(f"`{warning}`" for warning in summary.get("warnings") or []) or "-"
        lines.append(
            f"| {target['name']} | {summary['rows']} | {summary['document_count']} | "
            f"{summary['page_rate']} | {summary['article_or_ayat_rate']} | {summary['table_rate']} | {warnings} |"
        )

    for target in report["targets"]:
        summary = target["summary"]
        probe = target["evidence_probe"]
        lines.extend(
            [
                "",
                f"## {target['name']}",
                "",
                f"- Issuer: `{target['issuer']}`",
                f"- Title patterns: `{target['title_patterns']}`",
                f"- Rows: `{summary['rows']}`",
                f"- Documents: `{summary['document_count']}`",
                f"- Section types: `{summary['section_types']}`",
                f"- Citation quality: `{summary['citation_quality']}`",
                f"- Issue counts: `{summary['issue_counts']}`",
                f"- Warnings: `{summary['warnings']}`",
                "",
                "### Evidence Probe",
                "",
                f"- Query: `{probe['query']}`",
                f"- Confidence: `{(probe.get('confidence') or {}).get('label')}` score `{(probe.get('confidence') or {}).get('score')}`",
                "",
            ]
        )
        for citation in probe.get("top_citations") or []:
            lines.extend(
                [
                    f"- `{citation.get('issuer')}` `{citation.get('citation_quality')}` `{citation.get('section_type')}`: {citation.get('citation')}",
                    f"  - Snippet: {citation.get('snippet')}",
                ]
            )
        lines.extend(["", "### Extraction Examples", ""])
        for example in target.get("examples") or []:
            lines.extend(
                [
                    f"- `{example.get('citation_quality')}` `{example.get('section_type')}`: {example.get('citation')}",
                    f"  - Flags: `{example.get('flags')}`",
                    f"  - Text: {example.get('text')}",
                    "",
                ]
            )

    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_extraction_spot_check(args: argparse.Namespace) -> None:
    source_path = Path(args.source_corpus) if args.source_corpus else SOURCE_CORPUS_PATH
    if not source_path.exists():
        raise SystemExit(f"Missing source corpus: {source_path}")
    REPORTS_DIR.mkdir(exist_ok=True)
    report = build_extraction_spot_check(source_path)
    md_path = REPORTS_DIR / "extraction_spot_check.md"
    json_path = REPORTS_DIR / "extraction_spot_check.json"
    write_extraction_spot_check(report, md_path, json_path)
    print(f"Wrote {md_path.relative_to(ROOT)}")
    print(f"Wrote {json_path.relative_to(ROOT)}")
