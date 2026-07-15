from __future__ import annotations

import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

import pytest

from thinking_layer.config.paths import ROOT
from thinking_layer.corpus.builder import build_corpus
from thinking_layer.domain.legal import LEGAL_DOCUMENT_SCHEMA_VERSION, LegalDocumentV1


FRESH_FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "fresh_liteparse"


def _write_raw(
    directory: Path,
    file_name: str,
    file_id: str,
    markdown: str,
    *,
    ocr_enabled: bool = False,
) -> Path:
    path = directory / file_name
    path.write_text(
        json.dumps(
            {
                "file_id": file_id,
                "liteparse_options": {"ocr_enabled": ocr_enabled},
                "pages": [{"page_num": 1, "markdown": markdown}],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_rebuilds_clean_outputs_and_reports_ocr_coverage() -> None:
    with TemporaryDirectory(dir=ROOT) as temporary:
        root = Path(temporary)
        raw_dir = root / "raw"
        output_dir = root / "corpus"
        raw_dir.mkdir()
        _write_raw(
            raw_dir,
            "amending.json",
            "fixture-pbi-15-7-2013",
            (
                "PERATURAN BANK INDONESIA NOMOR 15/7/PBI/2013\n"
                "PERUBAHAN ATAS PERATURAN BANK INDONESIA NOMOR 12/19/PBI/2010\n\n"
                "Pasal 1\n(1) Bank wajib melapor."
            ),
        )
        _write_raw(
            raw_dir,
            "prior.json",
            "fixture-pbi-12-19-2010",
            "PERATURAN BANK INDONESIA NOMOR 12/19/PBI/2010\n\nPasal 1\nBank wajib menjaga likuiditas.",
        )
        _write_raw(
            raw_dir,
            "excluded.json",
            "fixture-scan-only",
            "Pasal 1\nTidak diparse.",
            ocr_enabled=True,
        )
        exclusions = root / "ocr_needed.json"
        exclusions.write_text(json.dumps(["fixture-scan-only"]), encoding="utf-8")
        output_dir.mkdir()
        (output_dir / "stale.txt").write_text("obsolete", encoding="utf-8")

        result = build_corpus(
            raw_dir=raw_dir, output_dir=output_dir, ocr_needed_path=exclusions
        )

        assert result.audit.passed
        assert result.source_document_count == 2
        assert result.lifecycle_relation_count == 1
        assert result.skipped_ocr_file_ids == ("fixture-scan-only",)
        assert result.quarantined_sources == ()
        assert not (output_dir / "stale.txt").exists()
        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        assert manifest["eligible_document_count"] == 2
        assert manifest["skipped_ocr_file_ids"] == ["fixture-scan-only"]
        assert (output_dir / "legal_nodes.ndjson").exists()
        assert (output_dir / "contextual_units.ndjson").exists()
        assert result.schema_path.exists()
        assert (
            manifest["legal_document_schema_version"] == LEGAL_DOCUMENT_SCHEMA_VERSION
        )
        artifact = json.loads(
            (output_dir / "legal_documents.ndjson")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        assert (
            LegalDocumentV1.model_validate(artifact).schema_version
            == LEGAL_DOCUMENT_SCHEMA_VERSION
        )
        assert "legal_documents.ndjson" in manifest["outputs"]
        assert "legal_document_v1.schema.json" in manifest["outputs"]


def test_clean_build_accepts_every_representative_fresh_liteparse_fixture() -> None:
    with TemporaryDirectory(dir=ROOT) as temporary:
        root = Path(temporary)
        raw_dir = root / "raw"
        output_dir = root / "corpus"
        raw_dir.mkdir()
        fixtures = tuple(sorted(FRESH_FIXTURE_DIR.glob("*.json")))
        for fixture in fixtures:
            shutil.copyfile(fixture, raw_dir / fixture.name)
        exclusions = root / "ocr_needed.json"
        exclusions.write_text("[]", encoding="utf-8")

        result = build_corpus(
            raw_dir=raw_dir, output_dir=output_dir, ocr_needed_path=exclusions
        )

        artifacts = [
            LegalDocumentV1.model_validate(json.loads(line))
            for line in (output_dir / "legal_documents.ndjson")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        assert result.audit.passed
        assert result.source_document_count == len(fixtures)
        assert {artifact.source_document.role for artifact in artifacts} == {
            "primary_regulation",
            "explanation",
            "attachment",
            "circular",
            "secondary_faq",
        }
        assert any(
            block.kind == "table"
            for artifact in artifacts
            for block in artifact.source_blocks
        )
        assert any(
            block.kind == "list_item"
            for artifact in artifacts
            for block in artifact.source_blocks
        )
        assert all(
            "# " not in block.display_text and "**" not in block.display_text
            for artifact in artifacts
            for block in artifact.source_blocks
        )
        faq = next(
            artifact
            for artifact in artifacts
            if artifact.source_document.role == "secondary_faq"
        )
        assert all(node.legal_path.angka is None for node in faq.legal_nodes)


def test_reports_geometry_disagreements_and_quarantines_an_unanchored_source() -> None:
    with TemporaryDirectory(dir=ROOT) as temporary:
        root = Path(temporary)
        raw_dir = root / "raw"
        output_dir = root / "corpus"
        raw_dir.mkdir()
        (raw_dir / "mismatch.json").write_text(
            json.dumps(
                {
                    "contract": "thinking-layer-fresh-liteparse-v1",
                    "file_id": "fixture-geometry-mismatch",
                    "source_path": "downloads/peraturan-ojk/POJK 1.pdf",
                    "liteparse_options": {"ocr_enabled": False},
                    "pages": [
                        {
                            "page_num": 1,
                            "markdown": "PERATURAN OTORITAS JASA KEUANGAN\n\nPasal 1\nBank wajib melapor.",
                            "text": "PERATURAN OTORITAS JASA KEUANGAN\n\nPasal 1\nBank wajib melapor.",
                            "text_items": [
                                {
                                    "text": "tata letak berbeda",
                                    "x": 1,
                                    "y": 1,
                                    "width": 10,
                                    "height": 10,
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        exclusions = root / "ocr_needed.json"
        exclusions.write_text("[]", encoding="utf-8")

        result = build_corpus(
            raw_dir=raw_dir, output_dir=output_dir, ocr_needed_path=exclusions
        )

        assert result.source_document_count == 0
        assert result.quarantined_sources == (
            (
                "fixture-geometry-mismatch",
                "all parseable blocks failed geometry validation",
            ),
        )
        assert result.geometry_disagreements
        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        assert manifest["geometry_disagreement_count"] == len(
            result.geometry_disagreements
        )
        assert {entry["reason"] for entry in manifest["geometry_disagreements"]} == {
            "markdown_geometry_text_disagreement"
        }


def test_persists_failure_manifest_before_removing_staging_output() -> None:
    with TemporaryDirectory(dir=ROOT) as temporary:
        root = Path(temporary)
        raw_dir = root / "raw"
        output_dir = root / "corpus"
        raw_dir.mkdir()
        _write_raw(
            raw_dir,
            "dangling.json",
            "fixture-dangling",
            "Pasal 1\nKetentuan berlaku berdasarkan",
        )
        exclusions = root / "ocr_needed.json"
        exclusions.write_text("[]", encoding="utf-8")

        with pytest.raises(ValueError, match="corpus structural audit failed"):
            build_corpus(
                raw_dir=raw_dir, output_dir=output_dir, ocr_needed_path=exclusions
            )

        failure_path = root / "corpus.failure.json"
        failure = json.loads(failure_path.read_text(encoding="utf-8"))
        assert failure["status"] == "failed"
        assert "dangling_fragment" in failure["finding_codes"]
        assert "build_failure" in failure["finding_codes"]
        assert failure["counts"]["raw_input_count"] == 1
        assert failure["raw_input_sha256"]
        assert not output_dir.exists()
        assert not list(root.glob(".corpus.*"))


def test_persists_failure_manifest_when_fresh_raw_input_is_missing() -> None:
    with TemporaryDirectory(dir=ROOT) as temporary:
        root = Path(temporary)
        raw_dir = root / "raw"
        output_dir = root / "corpus"
        raw_dir.mkdir()
        exclusions = root / "ocr_needed.json"
        exclusions.write_text("[]", encoding="utf-8")

        with pytest.raises(ValueError, match="no fresh raw JSON files"):
            build_corpus(
                raw_dir=raw_dir, output_dir=output_dir, ocr_needed_path=exclusions
            )

        failure = json.loads((root / "corpus.failure.json").read_text(encoding="utf-8"))
        assert failure["finding_codes"] == ["build_failure"]
        assert failure["counts"]["raw_input_count"] == 0
