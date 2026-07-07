from __future__ import annotations

import argparse
import json
from typing import Any

from .audit import build_audit, write_audit_markdown
from .metadata import (
    DownloadIndex,
    SourceRecord,
    build_download_index,
    classify_file_role,
    file_entries,
    load_records,
    normalized_metadata,
    resolve_saved_path,
    sha256_file,
)
from ..common.text import slugify
from ..config.paths import PROCESSED_DIR, REPORTS_DIR, ROOT

def write_processed(records: list[SourceRecord], download_index: DownloadIndex, include_hash: bool) -> None:
    PROCESSED_DIR.mkdir(exist_ok=True)
    canonical_path = PROCESSED_DIR / "canonical_regulations.ndjson"
    file_manifest_path = PROCESSED_DIR / "file_manifest.ndjson"

    # Baseline documents: OJK from peraturan-ojk, BI from ease-bi. Sikepo stays
    # available for later enrichment and duplicate analysis.
    primary_sources = {"peraturan-ojk", "ease-bi"}

    with canonical_path.open("w", encoding="utf-8") as canonical_out, file_manifest_path.open(
        "w", encoding="utf-8"
    ) as file_out:
        for record in records:
            meta = normalized_metadata(record)
            entries = file_entries(record)

            if record.source in primary_sources:
                canonical_doc = {
                    **meta,
                    "primary_source": record.source,
                    "source_priority": "primary",
                    "sikepo_enrichment_status": "not_applied",
                    "file_count": len(entries),
                    "citation_policy": {
                        "primary_first": True,
                        "required_best_effort_fields": ["document", "page", "pasal", "ayat"],
                        "must_say_not_found_when_unsure": True,
                    },
                }
                canonical_out.write(json.dumps(canonical_doc, ensure_ascii=False) + "\n")

            for index, entry in enumerate(entries):
                resolved_path, exists, error = resolve_saved_path(entry.get("saved_path"), download_index)
                file_path = ROOT / resolved_path if resolved_path else None
                manifest = {
                    "file_id": slugify(f"{meta['source']}:{meta['source_id']}:{index}:{entry.get('label') or ''}"),
                    "canonical_id": meta["canonical_id"],
                    "source": record.source,
                    "source_id": meta["source_id"],
                    "issuer": meta["issuer"],
                    "title": meta["title"],
                    "regulation_type": meta["regulation_type"],
                    "number": meta["number"],
                    "year": meta["year"],
                    "file_role": classify_file_role(record.source, entry),
                    "source_kind": entry.get("kind"),
                    "label": entry.get("label"),
                    "content_type": entry.get("content_type"),
                    "source_url": entry.get("source_url"),
                    "final_url": entry.get("final_url"),
                    "saved_path": entry.get("saved_path"),
                    "resolved_path": resolved_path,
                    "exists": exists,
                    "error": error,
                    "size_bytes": file_path.stat().st_size if exists and file_path else None,
                    "sha256": sha256_file(file_path) if include_hash and exists and file_path else None,
                }
                file_out.write(json.dumps(manifest, ensure_ascii=False) + "\n")

def cmd_audit(args: argparse.Namespace) -> None:
    records = load_records()
    download_index = build_download_index()
    REPORTS_DIR.mkdir(exist_ok=True)
    audit = build_audit(records, download_index)
    audit_json = REPORTS_DIR / "corpus_audit.json"
    audit_md = REPORTS_DIR / "corpus_audit.md"
    audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_audit_markdown(audit, audit_md)
    print(f"Wrote {audit_json.relative_to(ROOT)}")
    print(f"Wrote {audit_md.relative_to(ROOT)}")

def cmd_build(args: argparse.Namespace) -> None:
    records = load_records()
    download_index = build_download_index()
    write_processed(records, download_index, include_hash=args.hash)
    print("Wrote processed/canonical_regulations.ndjson")
    print("Wrote processed/file_manifest.ndjson")

def cmd_all(args: argparse.Namespace) -> None:
    cmd_audit(args)
    cmd_build(args)
