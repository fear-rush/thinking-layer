from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from thinking_layer.corpus.extraction import (
    LITEPARSE_OPTIONS,
    build_source_inventory,
    extract_fresh_raw,
)


def _record(
    root: Path, *, source: str, record_id: str, label: str, filename: str
) -> None:
    record_dir = root / "data" / source
    record_dir.mkdir(parents=True, exist_ok=True)
    (root / "downloads" / source).mkdir(parents=True, exist_ok=True)
    (root / "downloads" / source / filename).write_bytes(b"%PDF-1.7 fixture")
    (record_dir / f"{record_id}.json").write_text(
        json.dumps(
            {
                "record_id": record_id,
                "files": [
                    {
                        "label": label,
                        "saved_path": f"downloads/{source}/{filename}",
                        "final_url": f"https://example.test/{filename}",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _result() -> SimpleNamespace:
    return SimpleNamespace(
        text="# Peraturan\n\nPasal 1\nBank wajib melapor.",
        pages=[
            SimpleNamespace(
                page_num=1,
                width=612.0,
                height=792.0,
                text="Peraturan\nPasal 1\nBank wajib melapor.",
                markdown="# Peraturan\n\nPasal 1\nBank wajib melapor.",
                text_items=[
                    SimpleNamespace(
                        text="Pasal 1",
                        x=10.0,
                        y=20.0,
                        width=30.0,
                        height=12.0,
                        font_name="Times",
                        font_size=12.0,
                        confidence=1.0,
                        rotation=0.0,
                        words=[
                            SimpleNamespace(
                                text="Pasal", x=10.0, y=20.0, width=20.0, height=12.0
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_inventory_joins_downloads_to_source_records_with_stable_ids(
    tmp_path: Path,
) -> None:
    _record(
        tmp_path,
        source="peraturan-ojk",
        record_id="pojk-1",
        label="POJK 1.pdf",
        filename="POJK 1.pdf",
    )

    inventory = build_source_inventory(
        downloads_dir=tmp_path / "downloads",
        source_records_dir=tmp_path / "data",
        root=tmp_path,
    )

    assert len(inventory) == 1
    row = inventory[0]
    assert row.file_id == "peraturan-ojk-pojk-1-0-pojk-1-pdf"
    assert row.source_path == "downloads/peraturan-ojk/POJK 1.pdf"
    assert row.source_url == "https://example.test/POJK 1.pdf"
    assert len(row.source_sha256) == 64


def test_inventory_rejects_downloaded_pdfs_without_source_records(
    tmp_path: Path,
) -> None:
    (tmp_path / "downloads").mkdir()
    (tmp_path / "downloads" / "unrecorded.pdf").write_bytes(b"%PDF-1.7")
    (tmp_path / "data").mkdir()

    with pytest.raises(ValueError, match="without source records"):
        build_source_inventory(
            downloads_dir=tmp_path / "downloads",
            source_records_dir=tmp_path / "data",
            root=tmp_path,
        )


def test_inventory_disambiguates_colliding_legacy_ids_without_changing_unique_ids(
    tmp_path: Path,
) -> None:
    _record(
        tmp_path,
        source="ease-bi",
        record_id="same-id",
        label="same.pdf",
        filename="first.pdf",
    )
    (tmp_path / "data" / "ease-bi" / "second.json").write_text(
        json.dumps(
            {
                "record_id": "same-id",
                "files": [
                    {
                        "label": "same.pdf",
                        "saved_path": "downloads/ease-bi/second.pdf",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "downloads" / "ease-bi" / "second.pdf").write_bytes(b"%PDF-1.7")

    inventory = build_source_inventory(
        downloads_dir=tmp_path / "downloads",
        source_records_dir=tmp_path / "data",
        root=tmp_path,
    )

    assert len({row.file_id for row in inventory}) == 2
    assert all(
        row.file_id.startswith("ease-bi-same-id-0-same-pdf-") for row in inventory
    )


def test_extraction_skips_ocr_sources_before_the_parser_and_emits_manifest(
    tmp_path: Path,
) -> None:
    _record(
        tmp_path,
        source="ease-bi",
        record_id="extract-me",
        label="text.pdf",
        filename="text.pdf",
    )
    _record(
        tmp_path,
        source="ease-bi",
        record_id="scan-only",
        label="scan.pdf",
        filename="scan.pdf",
    )
    exclusion_id = "ease-bi-scan-only-0-scan-pdf"
    exclusions = tmp_path / "ocr_needed.json"
    exclusions.write_text(
        json.dumps([{"file_id": exclusion_id, "reason": "requires OCR"}]),
        encoding="utf-8",
    )
    raw_dir = tmp_path / "processed" / "raw" / "liteparse"
    raw_dir.mkdir(parents=True)
    (raw_dir / "legacy.json").write_text("obsolete", encoding="utf-8")
    parsed_paths: list[Path] = []

    def parser(path: Path) -> SimpleNamespace:
        parsed_paths.append(path)
        return _result()

    result = extract_fresh_raw(
        downloads_dir=tmp_path / "downloads",
        source_records_dir=tmp_path / "data",
        raw_dir=raw_dir,
        ocr_needed_path=exclusions,
        parser=parser,
        root=tmp_path,
    )

    assert [path.name for path in parsed_paths] == ["text.pdf"]
    assert result.skipped_ocr_file_ids == (exclusion_id,)
    assert not (raw_dir / "legacy.json").exists()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_inventory_count"] == 2
    assert manifest["extracted_count"] == 1
    assert manifest["skipped_ocr"] == [
        {"file_id": exclusion_id, "reason": "requires OCR"}
    ]
    raw_paths = list((raw_dir / "documents").glob("*.json"))
    assert len(raw_paths) == 1
    raw = json.loads(raw_paths[0].read_text(encoding="utf-8"))
    assert raw["liteparse_options"] == LITEPARSE_OPTIONS
    assert raw["pages"][0]["markdown"].startswith("# Peraturan")
    assert raw["pages"][0]["text_items"][0]["words"][0]["text"] == "Pasal"


def test_extraction_fails_before_opening_any_source_when_ocr_id_is_unknown(
    tmp_path: Path,
) -> None:
    _record(
        tmp_path,
        source="ease-bi",
        record_id="text-only",
        label="text.pdf",
        filename="text.pdf",
    )
    exclusions = tmp_path / "ocr_needed.json"
    exclusions.write_text(json.dumps(["missing-file-id"]), encoding="utf-8")
    invoked = False

    def parser(_: Path) -> SimpleNamespace:
        nonlocal invoked
        invoked = True
        return _result()

    with pytest.raises(ValueError, match="missing from source inventory"):
        extract_fresh_raw(
            downloads_dir=tmp_path / "downloads",
            source_records_dir=tmp_path / "data",
            raw_dir=tmp_path / "raw",
            ocr_needed_path=exclusions,
            parser=parser,
            root=tmp_path,
        )
    assert not invoked
