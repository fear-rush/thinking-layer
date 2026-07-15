from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from thinking_layer.corpus.eligibility import OcrEligibility
from thinking_layer.corpus.parser import parse_saved_raw


class OcrExclusionTest(unittest.TestCase):
    def write_exclusions(self, directory: Path, payload: object) -> Path:
        path = directory / "ocr_needed.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_excludes_only_listed_file_ids_and_reports_coverage(self) -> None:
        with TemporaryDirectory() as temp:
            path = self.write_exclusions(
                Path(temp),
                [{"file_id": "scan-only", "reason": "image-only PDF"}],
            )
            eligibility = OcrEligibility.load(path)

            self.assertEqual(
                eligibility.eligible_file_ids(("text-pdf", "scan-only", "web-page")),
                ("text-pdf", "web-page"),
            )
            coverage = eligibility.coverage(("text-pdf", "scan-only", "web-page"))
            self.assertEqual(coverage.eligible_count, 2)
            self.assertEqual(coverage.skipped_ocr_file_ids, ("scan-only",))

    def test_rejects_ocr_derived_raw_records(self) -> None:
        with TemporaryDirectory() as temp:
            eligibility = OcrEligibility.load(self.write_exclusions(Path(temp), []))
            with self.assertRaisesRegex(ValueError, "used OCR"):
                eligibility.validate_raw_record(
                    {"file_id": "scan-only", "liteparse_options": {"ocr_enabled": True}}
                )

    def test_skips_listed_ocr_documents_before_they_are_parsed(self) -> None:
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            exclusions = self.write_exclusions(directory, ["scan-only"])
            raw_path = directory / "raw.json"
            raw_path.write_text(
                json.dumps(
                    {
                        "file_id": "scan-only",
                        "liteparse_options": {"ocr_enabled": True},
                        "pages": [{"page_num": 1, "markdown": "Pasal 1\\nTidak boleh diparse."}],
                    }
                ),
                encoding="utf-8",
            )

            self.assertIsNone(parse_saved_raw(raw_path, OcrEligibility.load(exclusions)))

    def test_requires_an_explicit_list_contract(self) -> None:
        with TemporaryDirectory() as temp, self.assertRaisesRegex(ValueError, "JSON list"):
            OcrEligibility.load(self.write_exclusions(Path(temp), {"file_ids": []}))


if __name__ == "__main__":
    unittest.main()
