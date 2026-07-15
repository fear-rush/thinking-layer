from __future__ import annotations

import argparse
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from thinking_layer.corpus.extraction_pipeline import (
    current_ocr_needed_file_ids,
    effective_liteparse_options,
    filter_manifests_for_args,
    refresh_extracted_metadata,
)


class ExtractionPipelineTests(unittest.TestCase):
    def test_liteparse_options_keep_ocr_disabled_by_default(self) -> None:
        args = argparse.Namespace(
            enable_ocr=False,
            ocr_server_url=None,
            ocr_language=None,
            ocr_dpi=None,
            ocr_num_workers=None,
        )

        options = effective_liteparse_options(
            args,
            {
                "output_format": "markdown",
                "quiet": True,
                "dpi": 150,
                "num_workers": 4,
                "image_mode": "off",
                "extract_links": True,
                "emit_word_boxes": True,
            },
            {
                "enabled": False,
                "server_url": "http://localhost:8829/ocr",
                "language": "id",
                "dpi": 200,
                "num_workers": 1,
            },
        )

        self.assertFalse(options["ocr_enabled"])
        self.assertIsNone(options["ocr_server_url"])
        self.assertIsNone(options["ocr_language"])
        self.assertEqual(options["dpi"], 150)
        self.assertEqual(options["num_workers"], 4)

    def test_liteparse_options_use_indonesian_paddleocr_profile_when_enabled(self) -> None:
        args = argparse.Namespace(
            enable_ocr=True,
            ocr_server_url=None,
            ocr_language=None,
            ocr_dpi=None,
            ocr_num_workers=None,
        )

        options = effective_liteparse_options(
            args,
            {
                "output_format": "markdown",
                "quiet": True,
                "dpi": 150,
                "num_workers": 4,
                "image_mode": "off",
                "extract_links": True,
                "emit_word_boxes": True,
            },
            {
                "enabled": False,
                "server_url": "http://localhost:8829/ocr",
                "language": "id",
                "dpi": 200,
                "num_workers": 1,
            },
        )

        self.assertTrue(options["ocr_enabled"])
        self.assertEqual(options["ocr_server_url"], "http://localhost:8829/ocr")
        self.assertEqual(options["ocr_language"], "id")
        self.assertEqual(options["dpi"], 200)
        self.assertEqual(options["num_workers"], 1)

    def test_liteparse_options_allow_cli_override(self) -> None:
        args = argparse.Namespace(
            enable_ocr=True,
            ocr_server_url="http://127.0.0.1:9000/ocr",
            ocr_language="en",
            ocr_dpi=240,
            ocr_num_workers=2,
        )

        options = effective_liteparse_options(
            args,
            {"output_format": "markdown"},
            {
                "enabled": False,
                "server_url": "http://localhost:8829/ocr",
                "language": "id",
                "dpi": 300,
                "num_workers": 1,
            },
        )

        self.assertEqual(options["ocr_server_url"], "http://127.0.0.1:9000/ocr")
        self.assertEqual(options["ocr_language"], "en")
        self.assertEqual(options["dpi"], 240)
        self.assertEqual(options["num_workers"], 2)

    def test_filter_manifests_by_file_id_and_path(self) -> None:
        manifests = [
            {"file_id": "a", "resolved_path": "downloads/one.pdf", "title": "One"},
            {"file_id": "b", "resolved_path": "downloads/slik-scan.pdf", "title": "SLIK Scan"},
            {"file_id": "c", "resolved_path": "downloads/other.pdf", "title": "Other"},
        ]

        by_id = filter_manifests_for_args(manifests, argparse.Namespace(file_id=["b"], path_contains=None))
        by_path = filter_manifests_for_args(manifests, argparse.Namespace(file_id=None, path_contains="slik"))

        self.assertEqual([row["file_id"] for row in by_id], ["b"])
        self.assertEqual([row["file_id"] for row in by_path], ["b"])

    def test_rebuild_exclusion_set_uses_current_ocr_needed_file_ids_only(self) -> None:
        with TemporaryDirectory() as directory:
            reports = Path(directory)
            (reports / "ocr_needed.json").write_text(
                '[{"file_id":"needs-ocr"},{"file_id":"parse-failed"},{"reason":"no_file_id"}]',
                encoding="utf-8",
            )
            with patch("thinking_layer.corpus.extraction_pipeline.REPORTS_DIR", reports):
                excluded = current_ocr_needed_file_ids()

        self.assertEqual(excluded, {"needs-ocr", "parse-failed"})

    def test_rebuild_refreshes_catalog_metadata_without_losing_raw_extraction(self) -> None:
        saved = {
            "file_id": "hosted-pbi",
            "resolved_path": "downloads/hosted-pbi.pdf",
            "issuer": "OJK",
            "raw_liteparse_path": "processed/raw/liteparse/hosted-pbi.json",
            "extraction_status": "extracted_ok",
        }
        current = {
            "file_id": "hosted-pbi",
            "resolved_path": "downloads/hosted-pbi.pdf",
            "issuer": "BI",
            "hosting_source_issuer": "OJK",
            "regulation_type": "PBI",
        }

        refreshed = refresh_extracted_metadata(
            saved,
            {("hosted-pbi", "downloads/hosted-pbi.pdf"): current},
        )

        self.assertEqual(refreshed["issuer"], "BI")
        self.assertEqual(refreshed["hosting_source_issuer"], "OJK")
        self.assertEqual(refreshed["raw_liteparse_path"], saved["raw_liteparse_path"])


if __name__ == "__main__":
    unittest.main()
