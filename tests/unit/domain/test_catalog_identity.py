from __future__ import annotations

import unittest

from thinking_layer.corpus.catalog import extract_instrument_identity


class CatalogIdentityTest(unittest.TestCase):
    def test_extracts_legacy_bi_identity_without_colliding_with_ojk(self) -> None:
        bi = extract_instrument_identity(
            "PERATURAN BANK INDONESIA NOMOR 15/7/PBI/2013 TENTANG GIRO WAJIB MINIMUM"
        )
        ojk = extract_instrument_identity(
            "PERATURAN OTORITAS JASA KEUANGAN NOMOR 15 TAHUN 2013 TENTANG REKSA DANA"
        )

        self.assertIsNotNone(bi)
        self.assertIsNotNone(ojk)
        assert bi is not None
        assert ojk is not None
        self.assertEqual((bi.issuer, bi.instrument_type, bi.number, bi.year), ("BI", "PBI", "15/7/PBI", 2013))
        self.assertNotEqual(bi.key, ojk.key)

    def test_extracts_ojk_surat_edaran_identity(self) -> None:
        identity = extract_instrument_identity(
            "SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 10/SEOJK.04/2025"
        )

        self.assertIsNotNone(identity)
        assert identity is not None
        self.assertEqual((identity.issuer, identity.instrument_type, identity.number, identity.year), ("OJK", "SEOJK", "10/SEOJK.04", 2025))

    def test_preserves_unclassified_source_documents_as_unknown(self) -> None:
        self.assertIsNone(extract_instrument_identity("PEDOMAN PENGAJUAN VERIFIKASI"))


if __name__ == "__main__":
    unittest.main()
