from __future__ import annotations

from pathlib import Path
import unittest

from thinking_layer.corpus.metadata import (
    DownloadIndex,
    SourceRecord,
    classify_file_role,
    file_entries,
    normalized_metadata,
    regulation_series_key,
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
                "date": "15 Juni 2021",
                "effective_date": "1 Juli 2021",
                "status": "Berlaku",
                "supersedes": ["PBI Nomor 20/6/PBI/2018"],
                "group_path": ["Sistem Pembayaran"],
            },
        )

        meta = normalized_metadata(record)

        self.assertEqual(meta["issuer"], "BI")
        self.assertEqual(meta["hosting_source_issuer"], "BI")
        self.assertEqual(meta["issuer_resolution_basis"], "regulation_type")
        self.assertFalse(meta["issuer_differs_from_host"])
        self.assertEqual(meta["regulation_type"], "PBI")
        self.assertEqual(meta["number"], "23/6/pbi/2021")
        self.assertEqual(meta["year"], "2021")
        self.assertEqual(meta["effective_date"], "2021-07-01")
        self.assertEqual(meta["issued_date"], "2021-06-15")
        self.assertEqual(meta["lifecycle_status"], "active")
        self.assertTrue(meta["is_current"])
        self.assertEqual(meta["supersedes"], ["PBI Nomor 20/6/PBI/2018"])
        self.assertEqual(meta["regulation_version_key"], meta["canonical_id"])
        self.assertEqual(regulation_series_key("BI", "PBI", "23/6/PBI/2021"), "bi-pbi-23-6-pbi")
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

    def test_ojk_hosted_pbi_uses_bi_regulation_identity(self) -> None:
        record = SourceRecord(
            source="peraturan-ojk",
            path=Path("data/peraturan-ojk/pbi.json"),
            payload={
                "law_id": "ojk-mirror-pbi",
                "title": "Peraturan Bank Indonesia Nomor 10/1/PBI/2008",
                "regulation_type": "PBI",
                "number": "10/1/PBI/2008",
                "year": "2008",
            },
        )

        meta = normalized_metadata(record)

        self.assertEqual(meta["issuer"], "BI")
        self.assertEqual(meta["hosting_source_issuer"], "OJK")
        self.assertEqual(meta["issuer_resolution_basis"], "regulation_type")
        self.assertTrue(meta["issuer_differs_from_host"])
        self.assertTrue(meta["canonical_id"].startswith("bi-pbi-"))
        self.assertTrue(meta["regulation_series_key"].startswith("bi-pbi-"))

    def test_regulation_identity_prevents_cross_issuer_host_leakage(self) -> None:
        ojk_on_bi_host = SourceRecord(
            source="ease-bi",
            path=Path("data/ease-bi/pojk.json"),
            payload={
                "record_id": "bi-mirror-pojk",
                "title": "POJK Nomor 6/POJK.07/2022",
                "regulation_type": "POJK",
                "number": "6/POJK.07/2022",
                "year": "2022",
            },
        )
        seojk = SourceRecord(
            source="peraturan-ojk",
            path=Path("data/peraturan-ojk/seojk.json"),
            payload={
                "law_id": "seojk-1",
                "title": "SEOJK Nomor 3/SEOJK.03/2021",
                "regulation_type": "SEOJK",
                "number": "3/SEOJK.03/2021",
                "year": "2021",
            },
        )

        self.assertEqual(normalized_metadata(ojk_on_bi_host)["issuer"], "OJK")
        self.assertEqual(normalized_metadata(seojk)["issuer"], "OJK")

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
