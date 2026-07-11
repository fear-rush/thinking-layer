from __future__ import annotations

import unittest

from thinking_layer.corpus.citations import (
    citation_quality_for_block,
    citation_text_for_block,
    normalize_source_corpus_block,
    section_type_for_block,
    source_priority_for_role,
)


class CitationTests(unittest.TestCase):
    def test_citation_quality_tracks_best_available_fields(self) -> None:
        base = {"document_title": "POJK Contoh"}

        self.assertEqual(citation_quality_for_block(base), "document_only")
        self.assertEqual(citation_quality_for_block({**base, "page_start": 3}), "document_page")
        self.assertEqual(
            citation_quality_for_block({**base, "page_start": 3, "pasal": "Pasal 2"}),
            "document_page_pasal",
        )
        self.assertEqual(
            citation_quality_for_block({**base, "page_start": 3, "pasal": "Pasal 2", "ayat": "(1)"}),
            "document_page_pasal_ayat",
        )
        self.assertEqual(
            citation_quality_for_block({**base, "page_start": 3, "pasal": "Pasal 2", "ayat": "(1)", "huruf": "huruf a"}),
            "document_page_pasal_ayat_huruf",
        )

    def test_normalize_source_corpus_block_preserves_citation_contract(self) -> None:
        row = normalize_source_corpus_block(
            {
                "block_id": "b1",
                "canonical_id": "doc-1",
                "file_id": "file-1",
                "issuer": "OJK",
                "source": "peraturan-ojk",
                "file_role": "primary_regulation",
                "document_title": "POJK Contoh",
                "regulation_type": "POJK",
                "number": "1/2026",
                "year": "2026",
                "regulation_version_key": "ojk-pojk-1-2026",
                "regulation_series_key": "ojk-pojk-1",
                "effective_date": "2026-02-01",
                "lifecycle_status": "active",
                "is_current": True,
                "page_start": 10,
                "page_end": 10,
                "block_type": "article",
                "pasal": "Pasal 4",
                "ayat": "(2)",
                "huruf": "huruf b",
                "text": "Pelaku usaha wajib menyampaikan laporan.",
            }
        )

        self.assertEqual(row["source_priority"], "primary")
        self.assertEqual(row["section_type"], "ayat")
        self.assertEqual(row["citation_quality"], "document_page_pasal_ayat_huruf")
        self.assertEqual(row["huruf"], "huruf b")
        self.assertEqual(row["citation"]["huruf"], "huruf b")
        self.assertEqual(row["citation"]["text"], "POJK Contoh, hlm. 10, Pasal 4, ayat (2), huruf b")
        self.assertEqual(row["regulation_version_key"], "ojk-pojk-1-2026")
        self.assertEqual(row["lifecycle_status"], "active")
        self.assertTrue(row["citation_policy"]["must_say_not_found_when_unsure"])

    def test_normalize_source_corpus_block_cleans_table_text(self) -> None:
        row = normalize_source_corpus_block(
            {
                "block_id": "b1",
                "canonical_id": "doc-1",
                "file_id": "file-1",
                "issuer": "OJK",
                "source": "peraturan-ojk",
                "file_role": "primary_regulation",
                "document_title": "POJK SLIK",
                "page_start": 4,
                "page_end": 4,
                "block_type": "table_or_row",
                "pasal": "Pasal 2",
                "ayat": "(1)",
                "text": "| a. | Bank Umum; | |---|---| | b. | BPR; |",
            }
        )

        self.assertEqual(row["text"], "a. Bank Umum; b. BPR")

    def test_section_type_and_priority_do_not_overstate_secondary_sources(self) -> None:
        self.assertEqual(source_priority_for_role("secondary_faq"), "secondary")
        self.assertEqual(section_type_for_block({"file_role": "secondary_faq", "block_type": "paragraph"}), "faq")
        self.assertEqual(section_type_for_block({"file_role": "attachment", "block_type": "paragraph"}), "attachment")
        self.assertEqual(citation_text_for_block({"citation": {"document": "Dokumen A"}}), "Dokumen A")


if __name__ == "__main__":
    unittest.main()
