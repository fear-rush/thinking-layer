from __future__ import annotations

import argparse
import json
from collections import defaultdict
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
    short_hash,
)
from ..common.text import slugify
from ..config.paths import PROCESSED_DIR, REPORTS_DIR, ROOT


def _preferred_primary_file_key(manifest: dict[str, Any]) -> tuple[int, str]:
    """Return a stable authority-first ordering for identical primary files."""
    issuer = str(manifest.get("issuer") or "")
    source = str(manifest.get("source") or "")
    authoritative_source = "ease-bi" if issuer == "BI" else "peraturan-ojk"
    return (0 if source == authoritative_source else 1, str(manifest.get("file_id") or ""))


def annotate_primary_file_duplicates(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    """Mark byte-identical primary copies without collapsing distinct texts.

    A canonical id alone is insufficient for deduplication: amendments,
    corrected publications, or genuinely different text must remain
    searchable.  Only primary files with the same canonical id *and* SHA-256
    content fingerprint are grouped.
    """
    exact_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for manifest in manifests:
        if manifest.get("file_role") != "primary_regulation":
            continue
        manifest.update(
            {
                "searchable_primary": True,
                "primary_duplicate_status": "unique",
                "primary_duplicate_group_id": None,
                "primary_duplicate_of_file_id": None,
                "primary_duplicate_group_size": 1,
                "primary_duplicate_reason": None,
            }
        )
        canonical_id = str(manifest.get("canonical_id") or "")
        fingerprint = str(manifest.get("dedupe_content_sha256") or manifest.get("sha256") or "")
        if canonical_id and fingerprint:
            exact_groups[(canonical_id, fingerprint)].append(manifest)

    duplicate_groups = 0
    duplicate_files = 0
    suppressed_files = 0
    for (canonical_id, fingerprint), group in exact_groups.items():
        if len(group) < 2:
            continue
        duplicate_groups += 1
        duplicate_files += len(group)
        suppressed_files += len(group) - 1
        preferred = min(group, key=_preferred_primary_file_key)
        group_id = f"primary-duplicate-{short_hash(f'{canonical_id}:{fingerprint}')}"
        for manifest in group:
            is_preferred = manifest is preferred
            manifest.update(
                {
                    "searchable_primary": is_preferred,
                    "primary_duplicate_status": "preferred" if is_preferred else "duplicate",
                    "primary_duplicate_group_id": group_id,
                    "primary_duplicate_of_file_id": None if is_preferred else preferred["file_id"],
                    "primary_duplicate_group_size": len(group),
                    "primary_duplicate_reason": "same_canonical_id_and_sha256",
                }
            )
    return {
        "exact_primary_duplicate_groups": duplicate_groups,
        "exact_primary_duplicate_files": duplicate_files,
        "suppressed_searchable_primary_files": suppressed_files,
    }


def populate_primary_duplicate_fingerprints(manifests: list[dict[str, Any]]) -> None:
    """Hash only plausible duplicate primaries when a full hash was not requested."""
    by_canonical: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for manifest in manifests:
        if manifest.get("file_role") == "primary_regulation" and manifest.get("exists"):
            by_canonical[str(manifest.get("canonical_id") or "")].append(manifest)

    for group in by_canonical.values():
        if len(group) < 2:
            continue
        by_size: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for manifest in group:
            size = manifest.get("size_bytes")
            if isinstance(size, int):
                by_size[size].append(manifest)
        for same_size in by_size.values():
            if len(same_size) < 2:
                continue
            for manifest in same_size:
                fingerprint = manifest.get("sha256")
                if not fingerprint:
                    resolved_path = manifest.get("resolved_path")
                    file_path = ROOT / str(resolved_path) if resolved_path else None
                    if file_path and file_path.is_file():
                        fingerprint = sha256_file(file_path)
                manifest["dedupe_content_sha256"] = fingerprint

def write_processed(records: list[SourceRecord], download_index: DownloadIndex, include_hash: bool) -> None:
    PROCESSED_DIR.mkdir(exist_ok=True)
    canonical_path = PROCESSED_DIR / "canonical_regulations.ndjson"
    file_manifest_path = PROCESSED_DIR / "file_manifest.ndjson"

    # Baseline documents: OJK from peraturan-ojk, BI from ease-bi. Sikepo stays
    # available for later enrichment and duplicate analysis.
    primary_sources = {"peraturan-ojk", "ease-bi"}

    canonical_docs: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    for record in records:
        meta = normalized_metadata(record)
        entries = file_entries(record)

        if record.source in primary_sources:
            canonical_docs.append(
                {
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
            )

        for index, entry in enumerate(entries):
            resolved_path, exists, error = resolve_saved_path(entry.get("saved_path"), download_index)
            file_path = ROOT / resolved_path if resolved_path else None
            manifests.append(
                {
                    "file_id": slugify(f"{meta['source']}:{meta['source_id']}:{index}:{entry.get('label') or ''}"),
                    "canonical_id": meta["canonical_id"],
                    "source": record.source,
                    "source_id": meta["source_id"],
                    "issuer": meta["issuer"],
                    "hosting_source_issuer": meta["hosting_source_issuer"],
                    "issuer_resolution_basis": meta["issuer_resolution_basis"],
                    "issuer_differs_from_host": meta["issuer_differs_from_host"],
                    "title": meta["title"],
                    "regulation_type": meta["regulation_type"],
                    "number": meta["number"],
                    "year": meta["year"],
                    "regulation_version_key": meta["regulation_version_key"],
                    "regulation_series_key": meta["regulation_series_key"],
                    "issued_date": meta["issued_date"],
                    "effective_date": meta["effective_date"],
                    "repeal_date": meta["repeal_date"],
                    "lifecycle_status": meta["lifecycle_status"],
                    "is_current": meta["is_current"],
                    "supersedes": meta["supersedes"],
                    "amends": meta["amends"],
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
            )

    populate_primary_duplicate_fingerprints(manifests)
    duplicate_summary = annotate_primary_file_duplicates(manifests)
    with canonical_path.open("w", encoding="utf-8") as canonical_out, file_manifest_path.open(
        "w", encoding="utf-8"
    ) as file_out:
        for canonical_doc in canonical_docs:
            canonical_out.write(json.dumps(canonical_doc, ensure_ascii=False) + "\n")
        for manifest in manifests:
            file_out.write(json.dumps(manifest, ensure_ascii=False) + "\n")

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "primary_duplicate_files.json").write_text(
        json.dumps(
            {
                **duplicate_summary,
                "groups": [
                    {
                        "group_id": manifest["primary_duplicate_group_id"],
                        "canonical_id": manifest["canonical_id"],
                        "group_size": manifest["primary_duplicate_group_size"],
                        "preferred_file_id": manifest["file_id"],
                        "reason": manifest["primary_duplicate_reason"],
                        "duplicate_file_ids": sorted(
                            item["file_id"]
                            for item in manifests
                            if item.get("primary_duplicate_group_id")
                            == manifest["primary_duplicate_group_id"]
                            and item.get("primary_duplicate_status") == "duplicate"
                        ),
                    }
                    for manifest in manifests
                    if manifest.get("primary_duplicate_status") == "preferred"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

def cmd_audit(_args: argparse.Namespace) -> None:
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
