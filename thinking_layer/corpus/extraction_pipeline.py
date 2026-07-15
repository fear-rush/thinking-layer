from __future__ import annotations

import argparse
import json
import shutil
import time
import traceback
from collections import Counter
from typing import Any

from .extraction import classify_extraction_status, extract_blocks, page_to_json, raw_output_path, safe_text
from ..common.io import read_ndjson_file
from ..config.heuristics import heuristic_section
from ..config.paths import PROCESSED_DIR, RAW_LITEPARSE_DIR, REPORTS_DIR, ROOT


def refresh_extracted_metadata(
    extracted: dict[str, Any],
    manifests_by_artifact: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Overlay current catalog metadata on a saved extraction record.

    Raw LiteParse pages are intentionally reusable, but issuer, lifecycle, and
    duplicate-resolution metadata can change when the catalog is rebuilt.  A
    legal-unit rebuild must therefore use the current manifest rather than
    freezing the metadata that happened to exist at extraction time.
    """
    key = (
        str(extracted.get("file_id") or ""),
        str(extracted.get("resolved_path") or ""),
    )
    manifest = manifests_by_artifact.get(key)
    if manifest is None:
        raise SystemExit(
            "Saved extraction has no matching current manifest row: "
            f"file_id={key[0]!r}, resolved_path={key[1]!r}"
        )
    return {**extracted, **manifest}

def write_ocr_reports(items: list[dict[str, Any]]) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    json_path = REPORTS_DIR / "ocr_needed.json"
    md_path = REPORTS_DIR / "ocr_needed.md"
    json_path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = ["# OCR Needed / Skipped Extraction", ""]
    lines.append(f"Total: {len(items)}")
    lines.append("")
    for item in items[:500]:
        status = item.get("status") or item.get("extraction_status")
        reason = item.get("reason") or item.get("extraction_reason")
        lines.append(
            f"- `{status}` `{reason}` | "
            f"{item.get('source')} | {item.get('file_role')} | "
            f"{item.get('title')} | `{item.get('resolved_path')}`"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def write_ndjson_file(path: Any, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")

def merge_replacement_rows(
    path: Any,
    replacement_rows: list[dict[str, Any]],
    file_ids: set[str],
) -> tuple[int, int]:
    existing_rows = read_ndjson_file(path) if path.exists() else []
    kept_rows = [row for row in existing_rows if row.get("file_id") not in file_ids]
    removed_count = len(existing_rows) - len(kept_rows)
    write_ndjson_file(path, [*kept_rows, *replacement_rows])
    return removed_count, len(replacement_rows)

def merge_replacement_ocr_items(
    replacement_items: list[dict[str, Any]],
    file_ids: set[str],
) -> tuple[int, int]:
    ocr_path = REPORTS_DIR / "ocr_needed.json"
    existing_items = json.load(ocr_path.open("r", encoding="utf-8")) if ocr_path.exists() else []
    kept_items = [item for item in existing_items if item.get("file_id") not in file_ids]
    removed_count = len(existing_items) - len(kept_items)
    write_ocr_reports([*kept_items, *replacement_items])
    return removed_count, len(replacement_items)

def write_extraction_summary() -> None:
    extracted_path = PROCESSED_DIR / "extracted_documents.ndjson"
    blocks_path = PROCESSED_DIR / "blocks.ndjson"
    manifest_path = PROCESSED_DIR / "file_manifest.ndjson"
    ocr_path = REPORTS_DIR / "ocr_needed.json"
    if not extracted_path.exists() or not blocks_path.exists():
        raise SystemExit("Missing extraction outputs. Run `python -m thinking_layer.cli extract` first.")

    extracted = read_ndjson_file(extracted_path)
    blocks = read_ndjson_file(blocks_path)
    ocr_items = json.load(ocr_path.open("r", encoding="utf-8")) if ocr_path.exists() else []

    canonical_manifest = [
        row for row in read_ndjson_file(manifest_path)
        if row.get("source") != "sikepo-ojk" and row.get("exists")
    ]
    extracted_ids = {row.get("file_id") for row in extracted}
    remaining = [row for row in canonical_manifest if row.get("file_id") not in extracted_ids]

    def counter(rows: list[dict[str, Any]], field: str) -> Counter[str]:
        return Counter(str(row.get(field)) for row in rows)

    block_citations = {
        "page": sum(1 for row in blocks if row.get("page_start")),
        "pasal": sum(1 for row in blocks if row.get("pasal")),
        "ayat": sum(1 for row in blocks if row.get("ayat")),
        "huruf": sum(1 for row in blocks if row.get("huruf")),
    }

    summary = {
        "documents": {
            "canonical_manifest_files": len(canonical_manifest),
            "extracted_rows": len(extracted),
            "unique_extracted_files": len(extracted_ids),
            "remaining_unextracted": len(remaining),
            "statuses": dict(counter(extracted, "extraction_status")),
            "sources": dict(counter(extracted, "source")),
            "roles": dict(counter(extracted, "file_role")),
        },
        "blocks": {
            "total": len(blocks),
            "sources": dict(counter(blocks, "source")),
            "roles": dict(counter(blocks, "file_role")),
            "types": dict(counter(blocks, "block_type")),
            "citation_fields_present": block_citations,
        },
        "skipped_or_needs_review": {
            "total": len(ocr_items),
            "reasons": dict(Counter(str(item.get("reason") or item.get("extraction_reason")) for item in ocr_items)),
            "remaining_unextracted": [
                {
                    "source": row.get("source"),
                    "file_role": row.get("file_role"),
                    "title": row.get("title"),
                    "resolved_path": row.get("resolved_path"),
                }
                for row in remaining[:100]
            ],
        },
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "extraction_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Extraction Summary",
        "",
        "## Documents",
        "",
        f"- Canonical manifest files: {summary['documents']['canonical_manifest_files']}",
        f"- Extracted rows: {summary['documents']['extracted_rows']}",
        f"- Unique extracted files: {summary['documents']['unique_extracted_files']}",
        f"- Remaining unextracted files: {summary['documents']['remaining_unextracted']}",
        f"- Statuses: `{summary['documents']['statuses']}`",
        f"- Sources: `{summary['documents']['sources']}`",
        f"- Roles: `{summary['documents']['roles']}`",
        "",
        "## Blocks",
        "",
        f"- Total blocks: {summary['blocks']['total']}",
        f"- Sources: `{summary['blocks']['sources']}`",
        f"- Roles: `{summary['blocks']['roles']}`",
        f"- Types: `{summary['blocks']['types']}`",
        f"- Citation fields present: `{summary['blocks']['citation_fields_present']}`",
        "",
        "## Skipped Or Needs Review",
        "",
        f"- Total skipped / OCR-needed / failed: {summary['skipped_or_needs_review']['total']}",
        f"- Reasons: `{summary['skipped_or_needs_review']['reasons']}`",
    ]
    if remaining:
        lines.extend(["", "### Remaining Unextracted", ""])
        for row in summary["skipped_or_needs_review"]["remaining_unextracted"]:
            lines.append(f"- {row['source']} | {row['file_role']} | {row['title']} | `{row['resolved_path']}`")

    (REPORTS_DIR / "extraction_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def should_extract_manifest(row: dict[str, Any], include_sikepo: bool) -> bool:
    if not row.get("exists"):
        return False
    return row.get("source") != "sikepo-ojk" or include_sikepo

def filter_manifests_for_args(manifests: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    file_ids = set(getattr(args, "file_id", None) or [])
    if file_ids:
        manifests = [row for row in manifests if row.get("file_id") in file_ids]
    path_contains = getattr(args, "path_contains", None)
    if path_contains:
        needle = str(path_contains).lower()
        manifests = [
            row
            for row in manifests
            if needle in str(row.get("resolved_path") or "").lower()
            or needle in str(row.get("title") or "").lower()
        ]
    return manifests

def effective_liteparse_options(args: argparse.Namespace, liteparse_config: dict[str, Any], ocr_config: dict[str, Any]) -> dict[str, Any]:
    ocr_enabled = bool(getattr(args, "enable_ocr", False) or ocr_config.get("enabled", False))
    ocr_server_url = getattr(args, "ocr_server_url", None) or ocr_config.get("server_url")
    ocr_language = getattr(args, "ocr_language", None) or ocr_config.get("language")
    dpi = float(
        getattr(args, "ocr_dpi", None)
        or (ocr_config.get("dpi") if ocr_enabled else liteparse_config.get("dpi"))
        or 150
    )
    num_workers = int(
        getattr(args, "ocr_num_workers", None)
        or (ocr_config.get("num_workers") if ocr_enabled else liteparse_config.get("num_workers"))
        or 4
    )
    if ocr_enabled and not ocr_server_url:
        raise SystemExit("OCR is enabled but no OCR server URL is configured. Use --ocr-server-url or resources/config/extraction_heuristics.json.")
    quiet = bool(liteparse_config.get("quiet", True))
    if bool(getattr(args, "verbose", False)):
        quiet = False
    return {
        "ocr_enabled": ocr_enabled,
        "ocr_server_url": str(ocr_server_url) if ocr_enabled and ocr_server_url else None,
        "ocr_language": str(ocr_language) if ocr_enabled and ocr_language else None,
        "output_format": str(liteparse_config.get("output_format", "markdown")),
        "quiet": quiet,
        "dpi": dpi,
        "preserve_very_small_text": bool(liteparse_config.get("preserve_very_small_text", False)),
        "num_workers": num_workers,
        "image_mode": str(liteparse_config.get("image_mode", "off")),
        "extract_links": bool(liteparse_config.get("extract_links", True)),
        "emit_word_boxes": bool(liteparse_config.get("emit_word_boxes", True)),
    }

def cmd_extract(args: argparse.Namespace) -> None:
    try:
        from liteparse import LiteParse
    except ImportError as exc:
        raise SystemExit("LiteParse is not installed. Run `uv add liteparse` first.") from exc

    manifest_path = PROCESSED_DIR / "file_manifest.ndjson"
    if not manifest_path.exists():
        raise SystemExit("Missing processed/file_manifest.ndjson. Run `python -m thinking_layer.cli build` first.")

    office_exts = {".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp"}
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    manifests = [row for row in read_ndjson_file(manifest_path) if should_extract_manifest(row, args.include_sikepo)]
    manifests = filter_manifests_for_args(manifests, args)
    if args.limit:
        manifests = manifests[: args.limit]
    replacement_file_ids = set(getattr(args, "file_id", None) or [])
    replace_existing = bool(getattr(args, "replace_existing", False))
    if replace_existing:
        if not replacement_file_ids:
            raise SystemExit("--replace-existing requires at least one --file-id.")
        if args.resume:
            raise SystemExit("--replace-existing cannot be used with --resume.")
        if args.limit:
            raise SystemExit("--replace-existing cannot be used with --limit; pass explicit --file-id values instead.")

    PROCESSED_DIR.mkdir(exist_ok=True)
    RAW_LITEPARSE_DIR.mkdir(parents=True, exist_ok=True)
    extracted_path = PROCESSED_DIR / "extracted_documents.ndjson"
    blocks_path = PROCESSED_DIR / "blocks.ndjson"
    extracted_write_path = PROCESSED_DIR / "extracted_documents.replace.tmp.ndjson" if replace_existing else extracted_path
    blocks_write_path = PROCESSED_DIR / "blocks.replace.tmp.ndjson" if replace_existing else blocks_path
    ocr_needed: list[dict[str, Any]] = []
    completed_file_ids: set[str] = set()

    if args.resume:
        for row in read_ndjson_file(extracted_path):
            if row.get("file_id"):
                completed_file_ids.add(row["file_id"])
        if completed_file_ids:
            manifests = [row for row in manifests if row.get("file_id") not in completed_file_ids]

    liteparse_config = heuristic_section("extraction_heuristics", "liteparse")
    ocr_config = heuristic_section("extraction_heuristics", "ocr")
    options = effective_liteparse_options(args, liteparse_config, ocr_config)
    if args.verbose:
        print("Extraction configuration:", flush=True)
        print(f"  manifest rows selected: {len(manifests)}", flush=True)
        print(f"  include_sikepo: {args.include_sikepo}", flush=True)
        print(f"  resume: {args.resume}", flush=True)
        print(f"  replace_existing: {replace_existing}", flush=True)
        print(f"  file_ids: {getattr(args, 'file_id', None) or []}", flush=True)
        print(f"  path_contains: {getattr(args, 'path_contains', None)}", flush=True)
        print(f"  max_pages: {args.max_pages}", flush=True)
        print(f"  target_pages: {args.target_pages}", flush=True)
        print(f"  liteparse_options: {json.dumps(options, ensure_ascii=False, sort_keys=True)}", flush=True)
    parser = LiteParse(
        ocr_enabled=options["ocr_enabled"],
        ocr_server_url=options["ocr_server_url"],
        ocr_language=options["ocr_language"],
        output_format=options["output_format"],
        quiet=options["quiet"],
        max_pages=args.max_pages,
        target_pages=args.target_pages,
        dpi=options["dpi"],
        preserve_very_small_text=options["preserve_very_small_text"],
        num_workers=options["num_workers"],
        image_mode=options["image_mode"],
        extract_links=options["extract_links"],
        emit_word_boxes=options["emit_word_boxes"],
    )

    processed_count = 0
    block_count = 0
    mode = "a" if args.resume and not replace_existing else "w"
    with extracted_write_path.open(mode, encoding="utf-8") as extracted_out, blocks_write_path.open(mode, encoding="utf-8") as blocks_out:
        for position, manifest in enumerate(manifests, start=1):
            if args.progress_every and (position == 1 or position % args.progress_every == 0):
                print(f"Extracting {position}/{len(manifests)}: {manifest.get('resolved_path')}", flush=True)
            if args.verbose:
                print(f"  file_id: {manifest.get('file_id')}", flush=True)
                print(f"  title: {manifest.get('title')}", flush=True)
                print(f"  source/role: {manifest.get('source')} / {manifest.get('file_role')}", flush=True)

            resolved_path = manifest.get("resolved_path")
            file_path = ROOT / resolved_path if resolved_path else None
            suffix = file_path.suffix.lower() if file_path else ""
            started = time.perf_counter()

            if suffix in office_exts and not soffice:
                item = {
                    **manifest,
                    "status": "skipped",
                    "reason": "libreoffice_not_found",
                }
                ocr_needed.append(item)
                if args.verbose:
                    print("  skipped: libreoffice_not_found", flush=True)
                continue

            try:
                if args.verbose:
                    size_bytes = file_path.stat().st_size if file_path and file_path.exists() else None
                    print(f"  parsing: {file_path}", flush=True)
                    print(f"  file_size_bytes: {size_bytes}", flush=True)
                result = parser.parse(str(file_path))
                pages = [page_to_json(page) for page in result.pages]
                total_text = safe_text(getattr(result, "text", "") or "\n".join(page.get("text", "") for page in pages))
                status, reason = classify_extraction_status(pages, len(total_text))
                empty_page_count = sum(1 for page in pages if len(safe_text(page.get("text") or page.get("markdown"))) < 20)
                raw_path = raw_output_path(manifest["file_id"])
                raw_payload = {
                    "file_id": manifest["file_id"],
                    "canonical_id": manifest["canonical_id"],
                    "resolved_path": resolved_path,
                    "status": status,
                    "reason": reason,
                    "liteparse_options": options,
                    "text": getattr(result, "text", "") or "",
                    "pages": pages,
                }
                raw_path.write_text(json.dumps(raw_payload, ensure_ascii=False) + "\n", encoding="utf-8")

                extracted_doc = {
                    **manifest,
                    "extraction_status": status,
                    "extraction_reason": reason,
                    "page_count": len(pages),
                    "text_length": len(total_text),
                    "empty_page_count": empty_page_count,
                    "raw_liteparse_path": str(raw_path.relative_to(ROOT)),
                    "ocr_enabled": options["ocr_enabled"],
                    "ocr_server_url": options["ocr_server_url"],
                    "ocr_language": options["ocr_language"],
                    "parse_dpi": options["dpi"],
                    "parse_num_workers": options["num_workers"],
                }
                extracted_out.write(json.dumps(extracted_doc, ensure_ascii=False) + "\n")
                processed_count += 1

                if status != "extracted_ok":
                    ocr_needed.append(extracted_doc)
                    if args.verbose:
                        elapsed = time.perf_counter() - started
                        print(
                            f"  result: {status} reason={reason} pages={len(pages)} "
                            f"empty_pages={empty_page_count} text_chars={len(total_text)} "
                            f"elapsed={elapsed:.2f}s raw={raw_path.relative_to(ROOT)}",
                            flush=True,
                        )
                    continue

                document_block_count = 0
                for block in extract_blocks(manifest, pages):
                    # Citation-critical QA should not consume blocks without page.
                    if block.get("page_start") is None:
                        continue
                    blocks_out.write(json.dumps(block, ensure_ascii=False) + "\n")
                    block_count += 1
                    document_block_count += 1
                if args.verbose:
                    elapsed = time.perf_counter() - started
                    print(
                        f"  result: {status} pages={len(pages)} empty_pages={empty_page_count} "
                        f"text_chars={len(total_text)} blocks={document_block_count} "
                        f"elapsed={elapsed:.2f}s raw={raw_path.relative_to(ROOT)}",
                        flush=True,
                    )
            except Exception as exc:
                item = {
                    **manifest,
                    "status": "parse_failed",
                    "reason": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(limit=3),
                }
                ocr_needed.append(item)
                if args.verbose:
                    elapsed = time.perf_counter() - started
                    print(f"  failed: {type(exc).__name__}: {exc} elapsed={elapsed:.2f}s", flush=True)

    if replace_existing:
        replacement_extracted = read_ndjson_file(extracted_write_path)
        replacement_blocks = read_ndjson_file(blocks_write_path)
        successful_file_ids = {row["file_id"] for row in replacement_extracted if row.get("file_id")}
        failed_file_ids = replacement_file_ids - successful_file_ids
        removed_docs, written_docs = merge_replacement_rows(extracted_path, replacement_extracted, successful_file_ids)
        removed_blocks, written_blocks = merge_replacement_rows(blocks_path, replacement_blocks, successful_file_ids)
        removed_ocr, written_ocr = merge_replacement_ocr_items(ocr_needed, replacement_file_ids)
        extracted_write_path.unlink(missing_ok=True)
        blocks_write_path.unlink(missing_ok=True)
        if failed_file_ids:
            print(
                "Preserved existing extracted rows and blocks for failed replacement file(s): "
                f"{', '.join(sorted(failed_file_ids))}",
                flush=True,
            )
        print(
            f"Replaced extracted rows for {len(replacement_file_ids)} file(s): "
            f"removed {removed_docs}, wrote {written_docs}",
            flush=True,
        )
        print(
            f"Replaced block rows for {len(replacement_file_ids)} file(s): "
            f"removed {removed_blocks}, wrote {written_blocks}",
            flush=True,
        )
        print(
            f"Replaced OCR report rows for {len(replacement_file_ids)} file(s): "
            f"removed {removed_ocr}, wrote {written_ocr}",
            flush=True,
        )
    else:
        write_ocr_reports(ocr_needed)
    print(f"Wrote {extracted_path.relative_to(ROOT)} ({processed_count} documents)")
    print(f"Wrote {blocks_path.relative_to(ROOT)} ({block_count} blocks)")
    print(f"Wrote reports/ocr_needed.json ({len(ocr_needed)} skipped/ocr-needed/failed files)")
    if args.resume:
        print(f"Resume skipped {len(completed_file_ids)} previously extracted files")
    if soffice:
        print(f"LibreOffice detected: {soffice}")
    else:
        print("LibreOffice not detected; Office documents were skipped.")

def cmd_report(_args: argparse.Namespace) -> None:
    ocr_items = json.load((REPORTS_DIR / "ocr_needed.json").open("r", encoding="utf-8")) if (REPORTS_DIR / "ocr_needed.json").exists() else []
    write_ocr_reports(ocr_items)
    write_extraction_summary()
    print("Wrote reports/extraction_summary.json")
    print("Wrote reports/extraction_summary.md")
    print("Refreshed reports/ocr_needed.json")
    print("Refreshed reports/ocr_needed.md")


def current_ocr_needed_file_ids() -> set[str]:
    """Read the migration exclusion set without invoking OCR or extraction."""
    path = REPORTS_DIR / "ocr_needed.json"
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise SystemExit("reports/ocr_needed.json must contain a list before rebuilding canonical legal-unit blocks.")
    return {str(row["file_id"]) for row in rows if isinstance(row, dict) and row.get("file_id")}


def cmd_rebuild_blocks(args: argparse.Namespace) -> None:
    extracted_path = PROCESSED_DIR / "extracted_documents.ndjson"
    blocks_path = PROCESSED_DIR / "blocks.ndjson"
    manifest_path = PROCESSED_DIR / "file_manifest.ndjson"
    if not extracted_path.exists() or not manifest_path.exists():
        raise SystemExit("Missing extracted documents or file manifest. Run the catalog build first.")

    manifests_by_artifact = {
        (str(row.get("file_id") or ""), str(row.get("resolved_path") or "")): row
        for row in read_ndjson_file(manifest_path)
    }
    target_file_ids = {str(value) for value in (getattr(args, "file_id", None) or [])}
    replace_existing = bool(getattr(args, "replace_existing", False))
    if target_file_ids and not replace_existing:
        raise SystemExit("Targeted rebuild-blocks requires --replace-existing.")
    if replace_existing and not target_file_ids:
        raise SystemExit("--replace-existing requires at least one --file-id.")

    block_count = 0
    document_count = 0
    missing_raw: list[dict[str, Any]] = []
    ocr_excluded_file_ids = current_ocr_needed_file_ids()
    ocr_skipped: list[str] = []
    rebuild_path = blocks_path.with_suffix(".rebuild.tmp.ndjson")
    try:
        extracted_rows = read_ndjson_file(extracted_path)
        if target_file_ids:
            extracted_rows = [
                row for row in extracted_rows
                if str(row.get("file_id") or "") in target_file_ids
            ]
            found_file_ids = {str(row.get("file_id") or "") for row in extracted_rows}
            missing_targets = sorted(target_file_ids - found_file_ids)
            if missing_targets:
                raise SystemExit(f"Unknown extracted --file-id target(s): {', '.join(missing_targets)}")

        replacements_by_file: dict[str, list[dict[str, Any]]] = {}
        rebuilt_documents: list[list[dict[str, Any]]] = []
        for saved_extraction in extracted_rows:
            extracted = refresh_extracted_metadata(saved_extraction, manifests_by_artifact)
            if extracted.get("extraction_status") != "extracted_ok":
                continue
            file_id = str(extracted.get("file_id") or "")
            if file_id in ocr_excluded_file_ids:
                ocr_skipped.append(file_id)
                continue
            raw_path_value = extracted.get("raw_liteparse_path")
            raw_path = ROOT / raw_path_value if raw_path_value else None
            if not raw_path or not raw_path.exists():
                missing_raw.append(extracted)
                continue
            raw_payload = json.loads(raw_path.read_text(encoding="utf-8"))
            pages = raw_payload.get("pages") or []
            rebuilt = [
                block for block in extract_blocks(extracted, pages)
                if block.get("page_start") is not None
            ]
            replacements_by_file.setdefault(file_id, []).extend(rebuilt)
            rebuilt_documents.append(rebuilt)
            block_count += len(rebuilt)
            document_count += 1

        if target_file_ids and (ocr_skipped or missing_raw):
            raise SystemExit("Targeted rebuild refused because a requested file is OCR-excluded or missing saved raw JSON.")

        with rebuild_path.open("w", encoding="utf-8") as blocks_out:
            if target_file_ids:
                emitted: set[str] = set()
                for existing in read_ndjson_file(blocks_path):
                    file_id = str(existing.get("file_id") or "")
                    if file_id in target_file_ids:
                        if file_id not in emitted:
                            for replacement in replacements_by_file.get(file_id, []):
                                blocks_out.write(json.dumps(replacement, ensure_ascii=False) + "\n")
                            emitted.add(file_id)
                        continue
                    blocks_out.write(json.dumps(existing, ensure_ascii=False) + "\n")
                for file_id in sorted(target_file_ids - emitted):
                    for replacement in replacements_by_file.get(file_id, []):
                        blocks_out.write(json.dumps(replacement, ensure_ascii=False) + "\n")
            else:
                for rebuilt in rebuilt_documents:
                    for block in rebuilt:
                        blocks_out.write(json.dumps(block, ensure_ascii=False) + "\n")
        rebuild_path.replace(blocks_path)
    except BaseException:
        rebuild_path.unlink(missing_ok=True)
        raise

    write_extraction_summary()
    action = "Replaced" if target_file_ids else "Rebuilt"
    print(f"{action} {blocks_path.relative_to(ROOT)} ({block_count} blocks from {document_count} documents)")
    if ocr_skipped:
        listed = ", ".join(sorted(ocr_skipped)[:20])
        suffix = " ..." if len(ocr_skipped) > 20 else ""
        print(f"Skipped {len(ocr_skipped)} document(s) listed in reports/ocr_needed.json: {listed}{suffix}")
    if missing_raw:
        print(f"Skipped {len(missing_raw)} extracted documents with missing raw LiteParse JSON")
