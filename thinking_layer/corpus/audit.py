from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .metadata import DownloadIndex, SourceRecord, file_entries, normalized_metadata, resolve_saved_path
from ..config.paths import DOWNLOADS_DIR
from ..common.text import normalize_space


def build_audit(records: list[SourceRecord], download_index: DownloadIndex) -> dict[str, Any]:
    by_source = Counter(record.source for record in records)
    missing_required: dict[str, Counter[str]] = defaultdict(Counter)
    files_by_source: dict[str, Counter[str]] = defaultdict(Counter)
    file_roles = Counter()
    missing_files: list[dict[str, Any]] = []
    duplicate_candidates: dict[str, list[dict[str, str | None]]] = defaultdict(list)

    for record in records:
        meta = normalized_metadata(record)
        for field in ("title", "number", "year", "effective_date"):
            if not meta.get(field):
                missing_required[record.source][field] += 1

        dedupe_key = "|".join(
            [
                meta.get("issuer") or "",
                meta.get("regulation_type") or "",
                meta.get("number") or "",
                meta.get("year") or "",
            ]
        )
        if meta.get("number"):
            duplicate_candidates[dedupe_key].append(
                {
                    "source": record.source,
                    "source_id": meta["source_id"],
                    "title": meta["title"],
                    "bank_slug": meta.get("bank_slug"),
                }
            )

        entries = file_entries(record)
        if not entries:
            files_by_source[record.source]["missing_file_entries"] += 1

        for entry in entries:
            role = normalize_space(entry.get("kind")) or "unknown"
            file_roles[role] += 1
            content_type = normalize_space(entry.get("content_type")) or "unknown"
            files_by_source[record.source][content_type] += 1
            resolved_path, exists, error = resolve_saved_path(entry.get("saved_path"), download_index)
            if not exists:
                missing_files.append(
                    {
                        "source": record.source,
                        "source_id": meta["source_id"],
                        "title": meta["title"],
                        "file_role": role,
                        "saved_path": entry.get("saved_path"),
                        "resolved_path": resolved_path,
                        "error": error,
                    }
                )

    duplicate_groups = [
        {"key": key, "count": len(items), "items": items[:10]}
        for key, items in duplicate_candidates.items()
        if len(items) > 1
    ]
    duplicate_groups.sort(key=lambda item: item["count"], reverse=True)

    download_extensions = Counter(
        path.suffix.lower().lstrip(".") or "no_ext"
        for path in DOWNLOADS_DIR.rglob("*")
        if path.is_file()
    )

    return {
        "summary": {
            "records_by_source": dict(sorted(by_source.items())),
            "download_extensions": dict(sorted(download_extensions.items())),
            "file_roles": dict(sorted(file_roles.items())),
            "missing_files_count": len(missing_files),
            "duplicate_candidate_groups": len(duplicate_groups),
        },
        "missing_required_fields": {
            source: dict(fields) for source, fields in sorted(missing_required.items())
        },
        "files_by_source": {
            source: dict(counter) for source, counter in sorted(files_by_source.items())
        },
        "missing_files": missing_files[:500],
        "duplicate_candidates": duplicate_groups[:200],
    }


def write_audit_markdown(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Corpus Audit",
        "",
        "## Summary",
        "",
    ]
    for key, value in audit["summary"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Missing Required Fields", ""])
    for source, fields in audit["missing_required_fields"].items():
        lines.append(f"- `{source}`: `{fields}`")

    lines.extend(["", "## Files By Source", ""])
    for source, fields in audit["files_by_source"].items():
        lines.append(f"- `{source}`: `{fields}`")

    lines.extend(["", "## Top Duplicate Candidates", ""])
    for group in audit["duplicate_candidates"][:25]:
        lines.append(f"- `{group['key']}`: {group['count']} records")
        for item in group["items"][:3]:
            lines.append(f"  - {item['source']} | {item.get('bank_slug') or '-'} | {item['title']}")

    lines.extend(["", "## Missing Files", ""])
    for item in audit["missing_files"][:50]:
        lines.append(f"- `{item['source']}` `{item['source_id']}` `{item['file_role']}`: {item['saved_path']}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
