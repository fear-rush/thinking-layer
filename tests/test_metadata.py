from __future__ import annotations

from pathlib import Path
import unittest

from thinking_layer.corpus.metadata import (
    DownloadIndex,
    SourceRecord,
    classify_file_role,
    file_entries,
    normalized_metadata,
    resolve_saved_path,
)


class MetadataTests(unittest.TestCase):
    def test_normalized_metadata_infers_bi_issuer_type_number_and_date(self) -> None:
        record = SourceRecord(
            source="ease-bi",
            path=Path("data/ease-bi/example.json"),
            payload={
                "record_id": "bi-1",
                "title": "PBI Nomor 23/6/PBI/2021 tentang Penyedia Jasa Pembayaran",
                "effective_date": "1 Juli 2021",
                "group_path": ["Sistem Pembayaran"],
            },
        )

        meta = normalized_metadata(record)

        self.assertEqual(meta["issuer"], "BI")
        self.assertEqual(meta["regulation_type"], "PBI")
        self.assertEqual(meta["number"], "23/6/pbi/2021")
        self.assertEqual(meta["year"], "2021")
        self.assertEqual(meta["effective_date"], "2021-07-01")
        self.assertEqual(meta["source_id"], "bi-1")

    def test_file_entries_support_single_file_payload(self) -> None:
        record = SourceRecord(
            source="peraturan-ojk",
            path=Path("data/peraturan-ojk/example.json"),
            payload={
                "tab_name": "dokumen",
                "file": {
                    "label": "PDF",
                    "saved_path": "downloads/peraturan-ojk/example.pdf",
                },
            },
        )

        entries = file_entries(record)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["kind"], "dokumen")

    def test_classify_file_role_keeps_secondary_and_attachments_out_of_primary(self) -> None:
        self.assertEqual(classify_file_role("peraturan-ojk", {"kind": "FAQ"}), "secondary_faq")
        self.assertEqual(classify_file_role("peraturan-ojk", {"kind": "Abstrak"}), "secondary_summary")
        self.assertEqual(classify_file_role("peraturan-ojk", {"label": "Lampiran I"}), "attachment")
        self.assertEqual(classify_file_role("ease-bi", {"kind": "Matriks Dokumen"}), "operational_requirement")
        self.assertEqual(classify_file_role("peraturan-ojk", {"kind": "Dokumen"}), "primary_regulation")

    def test_resolve_saved_path_reports_missing_metadata(self) -> None:
        resolved_path, exists, error = resolve_saved_path(None, DownloadIndex(by_basename={}))

        self.assertIsNone(resolved_path)
        self.assertFalse(exists)
        self.assertEqual(error, "missing_saved_path")


if __name__ == "__main__":
    unittest.main()
