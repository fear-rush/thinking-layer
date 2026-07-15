from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from thinking_layer.config.paths import ROOT
from thinking_layer.corpus.builder import build_corpus


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
