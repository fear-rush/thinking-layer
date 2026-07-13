from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from typing import Any

from .citations import normalize_source_corpus_block
from .metadata import SourceRecord, load_records, normalized_metadata, regulation_match_key
from ..common.io import iter_ndjson_file, read_ndjson_file
from ..config.paths import PROCESSED_DIR, REPORTS_DIR, ROOT, SOURCE_CORPUS_PATH


def source_corpus_block_key(row: dict[str, Any]) -> tuple[str, str] | None:
    """Return the citation identity that must be unique in the search index."""
    file_id = row.get("file_id")
    block_id = row.get("block_id")
    if not file_id or not block_id:
        return None
    return str(file_id), str(block_id)


def sikepo_metadata_coverage(records: list[SourceRecord]) -> dict[str, Any]:
    primary_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    sikepo_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    primary_by_loose_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    sikepo_by_loose_key: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record in records:
        meta = normalized_metadata(record)
        key = regulation_match_key(meta.get("issuer"), meta.get("regulation_type"), meta.get("number"), meta.get("year"))
        loose_key = regulation_match_key(
            meta.get("issuer"),
            meta.get("regulation_type"),
            meta.get("number"),
            meta.get("year"),
            include_year=False,
        )
        if not key:
            continue
        item = {
            "source": record.source,
            "source_id": meta.get("source_id"),
            "title": meta.get("title"),
            "number": meta.get("number"),
            "year": meta.get("year"),
            "bank_slug": meta.get("bank_slug"),
            "bank_name": meta.get("bank_name"),
        }
        if record.source == "peraturan-ojk":
            primary_by_key[key].append(item)
            if loose_key:
                primary_by_loose_key[loose_key].append(item)
        elif record.source == "sikepo-ojk":
            sikepo_by_key[key].append(item)
            if loose_key:
                sikepo_by_loose_key[loose_key].append(item)

    matched_keys = sorted(set(primary_by_key) & set(sikepo_by_key))
    primary_only_keys = sorted(set(primary_by_key) - set(sikepo_by_key))
    sikepo_only_keys = sorted(set(sikepo_by_key) - set(primary_by_key))
    loose_matched_keys = sorted(set(primary_by_loose_key) & set(sikepo_by_loose_key))
    loose_primary_only_keys = sorted(set(primary_by_loose_key) - set(sikepo_by_loose_key))
    loose_sikepo_only_keys = sorted(set(sikepo_by_loose_key) - set(primary_by_loose_key))

    return {
        "primary_ojk_keys": len(primary_by_key),
        "sikepo_keys": len(sikepo_by_key),
        "matched_keys": len(matched_keys),
        "primary_without_sikepo_metadata": len(primary_only_keys),
        "sikepo_without_primary_document": len(sikepo_only_keys),
        "loose_number_match": {
            "primary_ojk_keys": len(primary_by_loose_key),
            "sikepo_keys": len(sikepo_by_loose_key),
            "matched_keys": len(loose_matched_keys),
            "primary_without_sikepo_metadata": len(loose_primary_only_keys),
            "sikepo_without_primary_document": len(loose_sikepo_only_keys),
            "note": "Loose matching ignores year because OJK effective year and Sikepo issuance year can differ.",
        },
        "primary_without_sikepo_examples": [
            {"key": key, "items": primary_by_key[key][:3]}
            for key in primary_only_keys[:50]
        ],
        "sikepo_without_primary_examples": [
            {"key": key, "items": sikepo_by_key[key][:3]}
            for key in sikepo_only_keys[:50]
        ],
    }

def write_source_corpus_report(summary: dict[str, Any]) -> None:
    lines = [
        "# Source Corpus Baseline",
        "",
        "This report validates the normalized, citation-ready corpus used before retrieval and answer composition.",
        "",
        "## Summary",
        "",
        f"- Source corpus rows: {summary['rows']}",
        f"- Duplicate source blocks skipped: {summary['duplicate_block_rows_skipped']}",
        f"- Documents: {summary['documents']}",
        f"- Files: {summary['files']}",
        f"- Sources: `{summary['sources']}`",
        f"- Issuers: `{summary['issuers']}`",
        f"- Source priority: `{summary['source_priority']}`",
        f"- File roles: `{summary['file_roles']}`",
        f"- Section types: `{summary['section_types']}`",
        f"- Lifecycle status: `{summary['lifecycle_status']}`",
        f"- Citation quality: `{summary['citation_quality']}`",
        "",
        "## Sikepo Metadata Coverage",
        "",
        "Sikepo is treated as enrichment metadata, not as the primary OJK text source.",
        "",
        f"- Primary OJK regulation keys: {summary['sikepo_metadata_coverage']['primary_ojk_keys']}",
        f"- Sikepo regulation keys: {summary['sikepo_metadata_coverage']['sikepo_keys']}",
        f"- Strict matched keys: {summary['sikepo_metadata_coverage']['matched_keys']}",
        f"- Strict primary OJK keys without Sikepo metadata: {summary['sikepo_metadata_coverage']['primary_without_sikepo_metadata']}",
        f"- Strict Sikepo keys without primary OJK document: {summary['sikepo_metadata_coverage']['sikepo_without_primary_document']}",
        f"- Loose matched keys: {summary['sikepo_metadata_coverage']['loose_number_match']['matched_keys']}",
        f"- Loose primary OJK keys without Sikepo metadata: {summary['sikepo_metadata_coverage']['loose_number_match']['primary_without_sikepo_metadata']}",
        f"- Loose Sikepo keys without primary OJK document: {summary['sikepo_metadata_coverage']['loose_number_match']['sikepo_without_primary_document']}",
        "",
        "## Citation Contract",
        "",
        "- Answer composition may cite document and page when `citation_quality` is at least `document_page`.",
        "- Answer composition may cite Pasal/Ayat only when those fields are present on the evidence block.",
        "- For FAQ, abstrak, attachment, DOCX, and XLSX blocks, missing Pasal/Ayat is acceptable and must not be invented.",
        "- If evidence is weak or missing, the answer layer must say not found instead of filling gaps.",
    ]

    examples = summary["sikepo_metadata_coverage"].get("primary_without_sikepo_examples") or []
    if examples:
        lines.extend(["", "## Primary OJK Without Sikepo Examples", ""])
        for group in examples[:15]:
            item = group["items"][0]
            lines.append(f"- `{group['key']}` | {item.get('title')}")

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "source_corpus_baseline.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def cmd_build_source_corpus(args: argparse.Namespace) -> None:
    extracted_path = PROCESSED_DIR / "extracted_documents.ndjson"
    blocks_path = PROCESSED_DIR / "blocks.ndjson"
    if not extracted_path.exists() or not blocks_path.exists():
        raise SystemExit("Missing extraction outputs. Run `uv run python -m thinking_layer.cli extract` first.")

    extracted_ok = {
        row["file_id"]
        for row in read_ndjson_file(extracted_path)
        if row.get("extraction_status") == "extracted_ok" and row.get("file_id")
    }
    canonical_path = PROCESSED_DIR / "canonical_regulations.ndjson"
    canonical_metadata = (
        {
            row.get("canonical_id"): row
            for row in iter_ndjson_file(canonical_path)
            if row.get("canonical_id")
        }
        if canonical_path.exists()
        else {}
    )

    summary = {
        "rows": 0,
        "documents": 0,
        "files": 0,
        "sources": Counter(),
        "issuers": Counter(),
        "source_priority": Counter(),
        "file_roles": Counter(),
        "section_types": Counter(),
        "lifecycle_status": Counter(),
        "citation_quality": Counter(),
        "duplicate_block_rows_skipped": 0,
        "sikepo_metadata_coverage": sikepo_metadata_coverage(load_records()),
    }
    document_ids: set[str] = set()
    file_ids: set[str] = set()
    seen_block_keys: set[tuple[str, str]] = set()

    PROCESSED_DIR.mkdir(exist_ok=True)
    with SOURCE_CORPUS_PATH.open("w", encoding="utf-8") as out:
        for block in iter_ndjson_file(blocks_path):
            if block.get("file_id") not in extracted_ok:
                continue
            if not args.include_secondary and block.get("file_role") in {"secondary_faq", "secondary_summary"}:
                continue
            row = normalize_source_corpus_block(block, canonical_metadata.get(block.get("canonical_id")))
            if not row.get("text") or not row.get("citation", {}).get("page"):
                continue
            block_key = source_corpus_block_key(row)
            if block_key and block_key in seen_block_keys:
                summary["duplicate_block_rows_skipped"] += 1
                continue
            if block_key:
                seen_block_keys.add(block_key)
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

            summary["rows"] += 1
            if row.get("document_id"):
                document_ids.add(row["document_id"])
            if row.get("file_id"):
                file_ids.add(row["file_id"])
            summary["sources"][str(row.get("source"))] += 1
            summary["issuers"][str(row.get("issuer"))] += 1
            summary["source_priority"][str(row.get("source_priority"))] += 1
            summary["file_roles"][str(row.get("file_role"))] += 1
            summary["section_types"][str(row.get("section_type"))] += 1
            summary["lifecycle_status"][str(row.get("lifecycle_status") or "unknown")] += 1
            summary["citation_quality"][str(row.get("citation_quality"))] += 1

    summary["documents"] = len(document_ids)
    summary["files"] = len(file_ids)
    for key in ("sources", "issuers", "source_priority", "file_roles", "section_types", "lifecycle_status", "citation_quality"):
        summary[key] = dict(summary[key])

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "source_corpus_baseline.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_source_corpus_report(summary)

    print(f"Wrote {SOURCE_CORPUS_PATH.relative_to(ROOT)} ({summary['rows']} rows)")
    print("Wrote reports/source_corpus_baseline.json")
    print("Wrote reports/source_corpus_baseline.md")
