from __future__ import annotations

import json
from pathlib import Path

import pytest

from thinking_layer.corpus.eligibility import OcrEligibility
from thinking_layer.corpus.parser import parse_saved_raw
from thinking_layer.config.paths import OCR_NEEDED_PATH


def _write_exclusions(directory: Path, payload: object) -> Path:
    path = directory / "ocr_needed.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_excludes_only_listed_file_ids_and_reports_coverage(tmp_path: Path) -> None:
    path = _write_exclusions(
        tmp_path, [{"file_id": "scan-only", "reason": "image-only PDF"}]
    )
    eligibility = OcrEligibility.load(path)

    assert eligibility.eligible_file_ids(("text-pdf", "scan-only", "web-page")) == (
        "text-pdf",
        "web-page",
    )
    coverage = eligibility.coverage(("text-pdf", "scan-only", "web-page"))
    assert coverage.eligible_count == 2
    assert coverage.skipped_ocr_file_ids == ("scan-only",)


def test_rejects_ocr_derived_raw_records(tmp_path: Path) -> None:
    eligibility = OcrEligibility.load(_write_exclusions(tmp_path, []))

    with pytest.raises(ValueError, match="used OCR"):
        eligibility.validate_raw_record(
            {"file_id": "scan-only", "liteparse_options": {"ocr_enabled": True}}
        )


def test_skips_listed_ocr_documents_before_they_are_parsed(tmp_path: Path) -> None:
    exclusions = _write_exclusions(tmp_path, ["scan-only"])
    raw_path = tmp_path / "raw.json"
    raw_path.write_text(
        json.dumps(
            {
                "file_id": "scan-only",
                "liteparse_options": {"ocr_enabled": True},
                "pages": [{"page_num": 1, "markdown": "Pasal 1\nTidak boleh diparse."}],
            }
        ),
        encoding="utf-8",
    )

    assert parse_saved_raw(raw_path, OcrEligibility.load(exclusions)) is None


def test_requires_an_explicit_list_contract(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="JSON list"):
        OcrEligibility.load(_write_exclusions(tmp_path, {"file_ids": []}))


def test_authoritative_ocr_report_lists_pre_extraction_exclusions() -> None:
    exclusions = OcrEligibility.load(OCR_NEEDED_PATH).exclusions

    assert exclusions
    assert len({entry.file_id for entry in exclusions}) == len(exclusions)
    assert all(
        entry.reason == "requires OCR; skipped before fresh LiteParse extraction"
        for entry in exclusions
    )
