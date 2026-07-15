from __future__ import annotations

import unittest

from thinking_layer.corpus.citations import (
    citation_quality_for_block,
    citation_text_for_block,
    normalize_source_corpus_block,
    section_type_for_block,
    source_priority_for_role,
)
from thinking_layer.corpus.source_corpus import (
    is_source_corpus_eligible,
    source_corpus_block_key,
    source_corpus_exclusion_reason,
)


def v2_block(*, path: dict[str, str] | None = None, page: int | None = 3, **overrides: object) -> dict[str, object]:
    legal_path = path or {}
    block: dict[str, object] = {
        "chunk_schema_version": 2,
        "block_id": "node-1",
        "node_id": "node-1",
        "canonical_id": "doc-1",
        "file_id": "file-1",
        "issuer": "OJK",
        "source": "peraturan-ojk",
        "file_role": "primary_regulation",
        "document_title": "POJK Contoh",
        "page_start": page,
        "page_end": page,
        "block_type": "legal_unit",
        "legal_path": legal_path,
        "display_text": "Pelaku usaha wajib menyampaikan laporan.",
        "retrieval_text": "Pelaku usaha wajib menyampaikan laporan.",
        "legal_unit": {
            "type": "huruf" if legal_path.get("huruf") else "pasal",
            "legal_path": legal_path,
            "source_spans": [],
        },
    }
    block.update(overrides)
    return block


class CitationTests(unittest.TestCase):
    def test_citation_quality_tracks_explicit_v2_legal_path(self) -> None:
        self.assertEqual(citation_quality_for_block(v2_block(page=None)), "document_only")
        self.assertEqual(citation_quality_for_block(v2_block(path={})), "document_page")
        self.assertEqual(
            citation_quality_for_block(v2_block(path={"pasal": "Pasal 2"})),
            "document_page_pasal",
        )
        self.assertEqual(
            citation_quality_for_block(v2_block(path={"pasal": "Pasal 2", "ayat": "(1)"})),
            "document_page_pasal_ayat",
        )
        self.assertEqual(
            citation_quality_for_block(
                v2_block(path={"pasal": "Pasal 2", "ayat": "(1)", "huruf": "huruf a"})
            ),
            "document_page_pasal_ayat_huruf",
        )
        self.assertEqual(
            citation_quality_for_block(
                v2_block(
                    path={
                        "section": "IV. LAPORAN DEBITUR",
                        "point": "7",
                        "subpoint": "a",
                        "item": "1",
                    }
                )
            ),
            "document_page_section",
        )

    def test_outline_citation_uses_explicit_section_labels_without_pasal_aliases(self) -> None:
        row = normalize_source_corpus_block(
            v2_block(
                path={
                    "section": "IV. LAPORAN DEBITUR",
                    "point": "7",
                    "subpoint": "a",
                    "item": "1",
                },
                page=6,
                legal_unit={
                    "type": "item",
                    "legal_path": {
                        "section": "IV. LAPORAN DEBITUR",
                        "point": "7",
                        "subpoint": "a",
                        "item": "1",
                    },
                    "source_spans": [],
                },
            )
        )

        self.assertEqual(row["citation_quality"], "document_page_section")
        self.assertEqual(
            row["unit_path"],
            ["IV. LAPORAN DEBITUR", "7", "a", "1"],
        )
        self.assertEqual(
            row["citation"]["text"],
            "POJK Contoh, hlm. 6, IV. LAPORAN DEBITUR, butir 7, subbutir a, item 1",
        )
        self.assertIsNone(row["pasal"])
        self.assertIsNone(row["ayat"])
        self.assertIsNone(row["huruf"])

    def test_normalize_source_corpus_block_preserves_v2_citation_contract(self) -> None:
        row = normalize_source_corpus_block(
            v2_block(
                path={"pasal": "Pasal 4", "ayat": "(2)", "huruf": "huruf b"},
                page=10,
                regulation_type="POJK",
                number="1/2026",
                year="2026",
                regulation_version_key="ojk-pojk-1-2026",
                regulation_series_key="ojk-pojk-1",
                effective_date="2026-02-01",
                lifecycle_status="active",
                is_current=True,
            )
        )

        self.assertEqual(row["source_priority"], "primary")
        self.assertEqual(row["section_type"], "huruf")
        self.assertEqual(row["citation_quality"], "document_page_pasal_ayat_huruf")
        self.assertEqual(row["huruf"], "huruf b")
        self.assertEqual(row["citation"]["huruf"], "huruf b")
        self.assertEqual(row["citation"]["text"], "POJK Contoh, hlm. 10, Pasal 4, ayat (2), huruf b")
        self.assertEqual(row["regulation_version_key"], "ojk-pojk-1-2026")
        self.assertEqual(row["lifecycle_status"], "active")
        self.assertTrue(row["citation_policy"]["must_say_not_found_when_unsure"])

    def test_normalize_source_corpus_block_cleans_v2_table_text(self) -> None:
        row = normalize_source_corpus_block(
            v2_block(
                path={"pasal": "Pasal 2", "ayat": "(1)"},
                page=4,
                block_type="table_or_row",
                display_text="| a. | Bank Umum; | |---|---| | b. | BPR; |",
                retrieval_text="| a. | Bank Umum; | |---|---| | b. | BPR; |",
                legal_unit={"type": "table", "legal_path": {"pasal": "Pasal 2", "ayat": "(1)"}, "source_spans": []},
            )
        )

        self.assertEqual(row["text"], "a. Bank Umum; b. BPR")

    def test_non_v2_blocks_are_rejected_instead_of_inferred(self) -> None:
        with self.assertRaisesRegex(ValueError, "chunk_schema_version=2"):
            normalize_source_corpus_block({"block_id": "invalid", "document_title": "POJK", "text": "invalid"})

    def test_section_type_and_priority_use_v2_contract(self) -> None:
        self.assertEqual(source_priority_for_role("secondary_faq"), "secondary")
        self.assertEqual(section_type_for_block(v2_block(file_role="secondary_faq", legal_unit={"type": "huruf", "legal_path": {}, "source_spans": []})), "faq")
        self.assertEqual(section_type_for_block(v2_block(file_role="attachment", legal_unit={"type": "table", "legal_path": {}, "source_spans": []})), "attachment")
        self.assertEqual(citation_text_for_block(v2_block(document_title="Dokumen A", page_start=None, page_end=None)), "Dokumen A")

    def test_source_corpus_block_key_requires_both_citation_identifiers(self) -> None:
        self.assertEqual(source_corpus_block_key({"file_id": "file-1", "block_id": "block-1"}), ("file-1", "block-1"))
        self.assertIsNone(source_corpus_block_key({"file_id": "file-1"}))

    def test_duplicate_primary_copy_is_excluded_with_auditable_reason(self) -> None:
        block = v2_block(
            citation_admission="atomic_leaf",
            searchable_primary=False,
            primary_duplicate_status="duplicate",
            primary_duplicate_of_file_id="preferred-file",
        )

        self.assertFalse(is_source_corpus_eligible(block))
        self.assertEqual(source_corpus_exclusion_reason(block), "duplicate_primary_file")


if __name__ == "__main__":
    unittest.main()
