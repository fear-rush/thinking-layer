"""Fresh, reproducible OCR-disabled LiteParse extraction.

The downloaded PDFs and their harvested source records are the only input to this
module.  It deliberately has no reader for a prior raw-extraction directory.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import mkdtemp
from typing import Any

from ..config.paths import (
    DOWNLOADS_DIR,
    OCR_NEEDED_PATH,
    RAW_LITEPARSE_DIR,
    ROOT,
    SOURCE_RECORDS_DIR,
)
from .eligibility import OcrEligibility


_FILE_ID_SAFE = re.compile(r"[^a-z0-9]+")
_RAW_FILE_ID_LIMIT = 160
LITEPARSE_OPTIONS = {
    "ocr_enabled": False,
    "output_format": "markdown",
    "image_mode": "off",
    "extract_links": True,
    "emit_word_boxes": True,
    "quiet": True,
}


@dataclass(frozen=True)
class SourceInventoryRow:
    file_id: str
    source: str
    source_record_path: str
    source_url: str | None
    source_path: str
    source_sha256: str
    size_bytes: int


@dataclass(frozen=True)
class FreshExtractionResult:
    raw_dir: Path
    inventory_count: int
    extracted_file_ids: tuple[str, ...]
    skipped_ocr_file_ids: tuple[str, ...]
    failed: tuple[tuple[str, str], ...]
    manifest_path: Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1_048_576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _git_hash() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _slugify(value: str) -> str:
    return _FILE_ID_SAFE.sub("-", value.lower().strip()).strip("-")


def _source_identity(record: Mapping[str, Any], record_path: Path) -> str:
    for key in ("record_id", "law_id", "header_id", "source_url"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return record_path.stem


def _file_entries(record: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    files = record.get("files")
    if isinstance(files, list):
        return tuple(entry for entry in files if isinstance(entry, Mapping))
    file_entry = record.get("file")
    return (file_entry,) if isinstance(file_entry, Mapping) else ()


def _resolve_downloaded_path(root: Path, saved_path: str) -> Path:
    candidate = root / saved_path
    if candidate.is_file():
        return candidate
    if saved_path.startswith("downloads/ojk/"):
        candidate = root / saved_path.replace(
            "downloads/ojk/", "downloads/peraturan-ojk/", 1
        )
    return candidate


def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"source path must be inside repository: {path}") from error


def _iter_records(
    source_records_dir: Path,
) -> Iterable[tuple[str, Path, Mapping[str, Any]]]:
    if not source_records_dir.is_dir():
        raise FileNotFoundError(
            f"source-record directory does not exist: {source_records_dir}"
        )
    for source_dir in sorted(
        path for path in source_records_dir.iterdir() if path.is_dir()
    ):
        for record_path in sorted(source_dir.glob("*.json")):
            try:
                payload = json.loads(record_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid source record: {record_path}") from error
            if not isinstance(payload, Mapping):
                raise ValueError(f"source record must be an object: {record_path}")
            yield source_dir.name, record_path, payload


def build_source_inventory(
    *,
    downloads_dir: Path = DOWNLOADS_DIR,
    source_records_dir: Path = SOURCE_RECORDS_DIR,
    root: Path = ROOT,
) -> tuple[SourceInventoryRow, ...]:
    """Join every downloaded PDF to exactly one source-record file entry."""

    if not downloads_dir.is_dir():
        raise FileNotFoundError(f"downloads directory does not exist: {downloads_dir}")
    candidates: list[tuple[str, str, str, str | None, str, str, int]] = []
    seen_source_paths: set[str] = set()

    for source, record_path, record in _iter_records(source_records_dir):
        source_identity = _source_identity(record, record_path)
        for index, entry in enumerate(_file_entries(record)):
            saved_path = entry.get("saved_path")
            if not isinstance(saved_path, str) or not saved_path.strip():
                continue
            source_path = _resolve_downloaded_path(root, saved_path)
            if source_path.suffix.lower() != ".pdf":
                continue
            if not source_path.is_file():
                raise FileNotFoundError(
                    f"source record references missing downloaded PDF: {saved_path}"
                )
            label = entry.get("label")
            base_file_id = _slugify(
                f"{source}:{source_identity}:{index}:{label if isinstance(label, str) else ''}"
            )
            relative_source_path = _relative_to_root(source_path, root)
            if relative_source_path in seen_source_paths:
                raise ValueError(
                    f"downloaded PDF maps to more than one source record: {relative_source_path}"
                )
            seen_source_paths.add(relative_source_path)
            source_url = entry.get("final_url") or entry.get("source_url")
            candidates.append(
                (
                    base_file_id,
                    source,
                    _relative_to_root(record_path, root),
                    source_url if isinstance(source_url, str) else None,
                    relative_source_path,
                    _sha256(source_path),
                    source_path.stat().st_size,
                )
            )

    downloaded_paths = {
        _relative_to_root(path, root)
        for path in downloads_dir.rglob("*")
        if path.is_file() and path.suffix.lower() == ".pdf"
    }
    missing_records = sorted(downloaded_paths - seen_source_paths)
    if missing_records:
        examples = ", ".join(missing_records[:5])
        raise ValueError(
            "downloaded PDFs without source records: "
            f"{len(missing_records)} (for example: {examples})"
        )
    if not candidates:
        raise ValueError("source inventory contains no downloaded PDFs")
    base_id_counts = Counter(candidate[0] for candidate in candidates)
    rows: list[SourceInventoryRow] = []
    for (
        base_file_id,
        source,
        source_record_path,
        source_url,
        source_path,
        source_sha256,
        size_bytes,
    ) in candidates:
        file_id = base_file_id
        if base_id_counts[base_file_id] > 1:
            identity = f"{source_record_path}\0{source_path}"
            file_id = f"{base_file_id}-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:12]}"
        rows.append(
            SourceInventoryRow(
                file_id=file_id,
                source=source,
                source_record_path=source_record_path,
                source_url=source_url,
                source_path=source_path,
                source_sha256=source_sha256,
                size_bytes=size_bytes,
            )
        )
    return tuple(sorted(rows, key=lambda row: row.file_id))


def _raw_filename(file_id: str) -> str:
    digest = hashlib.sha256(file_id.encode("utf-8")).hexdigest()[:12]
    return f"{_slugify(file_id)[:_RAW_FILE_ID_LIMIT]}-{digest}.json"


def _word_box_to_json(word: Any) -> dict[str, Any]:
    return {
        "text": getattr(word, "text", "") or "",
        "x": getattr(word, "x", None),
        "y": getattr(word, "y", None),
        "width": getattr(word, "width", None),
        "height": getattr(word, "height", None),
    }


def _page_to_json(page: Any) -> dict[str, Any]:
    text_items = getattr(page, "text_items", []) or []
    return {
        "page_num": getattr(page, "page_num", None),
        "width": getattr(page, "width", None),
        "height": getattr(page, "height", None),
        "text": getattr(page, "text", "") or "",
        "markdown": getattr(page, "markdown", "") or "",
        "text_items": [
            {
                "text": getattr(item, "text", "") or "",
                "x": getattr(item, "x", None),
                "y": getattr(item, "y", None),
                "width": getattr(item, "width", None),
                "height": getattr(item, "height", None),
                "font_name": getattr(item, "font_name", None),
                "font_size": getattr(item, "font_size", None),
                "confidence": getattr(item, "confidence", None),
                "rotation": getattr(item, "rotation", None),
                "words": [
                    _word_box_to_json(word)
                    for word in (getattr(item, "words", []) or [])
                ],
            }
            for item in text_items
        ],
    }


def _liteparse_version() -> str:
    try:
        return importlib.metadata.version("liteparse")
    except importlib.metadata.PackageNotFoundError as error:
        raise RuntimeError("LiteParse is not installed; run `uv sync` first") from error


def _parse_with_liteparse(source_path: Path) -> Any:
    from liteparse import LiteParse

    return LiteParse(**LITEPARSE_OPTIONS).parse(source_path)


def _publish(staging_dir: Path, raw_dir: Path) -> None:
    raw_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir.replace(raw_dir)


def extract_fresh_raw(
    *,
    downloads_dir: Path = DOWNLOADS_DIR,
    source_records_dir: Path = SOURCE_RECORDS_DIR,
    raw_dir: Path = RAW_LITEPARSE_DIR,
    ocr_needed_path: Path = OCR_NEEDED_PATH,
    parser: Callable[[Path], Any] | None = None,
    root: Path = ROOT,
) -> FreshExtractionResult:
    """Replace legacy raw data with a complete, OCR-disabled extraction run."""

    inventory = build_source_inventory(
        downloads_dir=downloads_dir, source_records_dir=source_records_dir, root=root
    )
    eligibility = OcrEligibility.load(ocr_needed_path)
    by_file_id = {row.file_id: row for row in inventory}
    missing_ocr_ids = sorted(
        {entry.file_id for entry in eligibility.exclusions} - set(by_file_id)
    )
    if missing_ocr_ids:
        raise ValueError(
            "OCR exclusion IDs missing from source inventory: "
            + ", ".join(missing_ocr_ids)
        )
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.parent.mkdir(parents=True, exist_ok=True)

    parser = parser or _parse_with_liteparse
    staging_dir = Path(mkdtemp(prefix=f".{raw_dir.name}.", dir=raw_dir.parent))
    documents_dir = staging_dir / "documents"
    documents_dir.mkdir()
    extracted: list[str] = []
    skipped: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    document_outputs: dict[str, str] = {}
    try:
        for row in inventory:
            if not eligibility.is_eligible(row.file_id):
                reason = next(
                    entry.reason or "listed in reports/ocr_needed.json"
                    for entry in eligibility.exclusions
                    if entry.file_id == row.file_id
                )
                skipped.append({"file_id": row.file_id, "reason": reason})
                continue
            source_path = root / row.source_path
            try:
                result = parser(source_path)
                pages = [_page_to_json(page) for page in getattr(result, "pages", [])]
                if not pages:
                    raise ValueError("LiteParse returned no pages")
                raw_record = {
                    "contract": "thinking-layer-fresh-liteparse-v1",
                    "file_id": row.file_id,
                    "source_path": row.source_path,
                    "source_url": row.source_url,
                    "source_sha256": row.source_sha256,
                    "liteparse_version": _liteparse_version(),
                    "liteparse_options": LITEPARSE_OPTIONS,
                    "text": getattr(result, "text", "") or "",
                    "pages": pages,
                }
                output_path = documents_dir / _raw_filename(row.file_id)
                output_path.write_text(
                    json.dumps(raw_record, ensure_ascii=False, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                extracted.append(row.file_id)
                document_outputs[row.file_id] = _sha256(output_path)
            except Exception as error:  # per-document failures are auditable output
                failures.append(
                    {
                        "file_id": row.file_id,
                        "reason": f"{type(error).__name__}: {error}",
                    }
                )

        accounted_file_ids = {
            *extracted,
            *(entry["file_id"] for entry in skipped),
            *(entry["file_id"] for entry in failures),
        }
        if len(accounted_file_ids) != len(inventory):
            raise RuntimeError(
                "fresh extraction manifest does not account for every source"
            )

        inventory_json = [asdict(row) for row in inventory]
        (staging_dir / "inventory.json").write_text(
            json.dumps(inventory_json, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        manifest = {
            "contract": "thinking-layer-fresh-liteparse-v1",
            "created_at": datetime.now(UTC).isoformat(),
            "git_hash": _git_hash(),
            "liteparse_version": _liteparse_version(),
            "liteparse_options": LITEPARSE_OPTIONS,
            "source_inventory_sha256": _json_hash(inventory_json),
            "source_inventory_count": len(inventory),
            "extracted_file_ids": extracted,
            "extracted_count": len(extracted),
            "skipped_ocr": skipped,
            "skipped_ocr_count": len(skipped),
            "failed": failures,
            "failed_count": len(failures),
            "output_sha256": document_outputs,
        }
        (staging_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _publish(staging_dir, raw_dir)
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    return FreshExtractionResult(
        raw_dir=raw_dir,
        inventory_count=len(inventory),
        extracted_file_ids=tuple(extracted),
        skipped_ocr_file_ids=tuple(entry["file_id"] for entry in skipped),
        failed=tuple((entry["file_id"], entry["reason"]) for entry in failures),
        manifest_path=raw_dir / "manifest.json",
    )


def cmd_extract(args: argparse.Namespace) -> None:
    result = extract_fresh_raw(
        downloads_dir=Path(args.downloads_dir),
        source_records_dir=Path(args.source_records_dir),
        raw_dir=Path(args.raw_dir),
        ocr_needed_path=Path(args.ocr_needed),
    )
    print(
        json.dumps(
            {
                "raw_dir": result.raw_dir.as_posix(),
                "source_inventory_count": result.inventory_count,
                "extracted_count": len(result.extracted_file_ids),
                "skipped_ocr_count": len(result.skipped_ocr_file_ids),
                "skipped_ocr_file_ids": list(result.skipped_ocr_file_ids),
                "failed_count": len(result.failed),
                "manifest": result.manifest_path.as_posix(),
            },
            ensure_ascii=False,
        )
    )
