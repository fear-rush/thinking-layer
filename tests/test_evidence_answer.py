from __future__ import annotations

import unittest
from unittest.mock import patch

from thinking_layer.answer.composer import answer_item_rank, answer_status_for_pack, compose_template_answer, evidence_claim_text, is_usable_answer_claim, join_context_fragments
from thinking_layer.retrieval.evidence import evidence_confidence, evidence_item


class EvidenceAnswerTests(unittest.TestCase):
    def test_weak_evidence_requires_not_found(self) -> None:
        confidence = evidence_confidence([], ["OJK"], {"entities": [], "topics": []}, "aturan planet mars")

        self.assertEqual(confidence["label"], "not_found")
        self.assertTrue(confidence["must_say_not_found"])

    def test_strong_evidence_is_answerable_with_citations(self) -> None:
        item = {
            "issuer": "OJK",
            "is_primary": True,
            "has_page": True,
            "has_article": True,
            "matched_exact_phrases": ["pelaporan"],
            "lexical_support": 0.9,
            "citation": {"document": "POJK Pelaporan", "page": 2, "pasal": "Pasal 1", "ayat": "(1)"},
            "snippet": "Bank wajib menyampaikan pelaporan kepada OJK.",
        }
        confidence = evidence_confidence(
            [item],
            ["OJK"],
            {"entities": ["bank"], "topics": ["reporting"]},
            "apa kewajiban bank terkait pelaporan OJK",
        )

        self.assertEqual(confidence["label"], "strong")
        self.assertFalse(confidence["must_say_not_found"])

    def test_compose_template_answer_refuses_when_pack_is_not_found(self) -> None:
        pack = {
            "query": "aturan planet mars",
            "confidence": {"label": "weak", "score": 0.1, "must_say_not_found": True},
            "documents": [],
            "answer_policy": {"must_say_not_found_when_unsure": True},
        }

        answer = compose_template_answer(pack)

        self.assertEqual(answer["status"], "not_found")
        self.assertEqual(answer["citation_count"], 0)
        self.assertIn("Tidak ditemukan", answer["answer"])

    def test_answer_status_maps_partial_confidence(self) -> None:
        self.assertEqual(
            answer_status_for_pack({"confidence": {"label": "partial", "must_say_not_found": False}}),
            "partial",
        )
        self.assertEqual(
            answer_status_for_pack({"confidence": {"label": "strong", "must_say_not_found": False}}),
            "answerable",
        )

    def test_compose_template_answer_prefers_substantive_evidence_over_boilerplate(self) -> None:
        pack = {
            "query": "aturan penyelenggaraan usaha perusahaan modal ventura",
            "confidence": {"label": "strong", "score": 0.98, "must_say_not_found": False},
            "plan": {"issuers": ["OJK"]},
            "documents": [
                {
                    "issuer": "OJK",
                    "document": "Penyelenggaraan Usaha Perusahaan Modal Ventura",
                    "source_priority": "primary",
                    "file_role": "primary_regulation",
                    "citations": [
                        {
                            "score": 99.0,
                            "support_score": 99.0,
                            "citation_quality": "document_page",
                            "section_type": "paragraph",
                            "citation": {
                                "document": "Penyelenggaraan Usaha Perusahaan Modal Ventura",
                                "page": 1,
                                "text": "Penyelenggaraan Usaha Perusahaan Modal Ventura, hlm. 1",
                            },
                            "snippet": "PERATURAN OTORITAS JASA KEUANGAN NOMOR 25 TAHUN 2023 DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : bahwa ...",
                        },
                        {
                            "score": 20.0,
                            "support_score": 20.0,
                            "citation_quality": "document_page_pasal_ayat",
                            "section_type": "ayat",
                            "citation": {
                                "document": "Penyelenggaraan Usaha Perusahaan Modal Ventura",
                                "page": 6,
                                "pasal": "Pasal 2",
                                "ayat": "(1)",
                                "text": "Penyelenggaraan Usaha Perusahaan Modal Ventura, hlm. 6, Pasal 2, ayat (1)",
                            },
                            "snippet": "Pasal 2 (1) PMV menyelenggarakan Usaha Modal Ventura sesuai kegiatan usaha yang diatur OJK.",
                        },
                    ],
                }
            ],
            "answer_policy": {"must_say_not_found_when_unsure": True},
        }

        answer = compose_template_answer(pack, max_documents=1, max_citations_per_document=2)

        self.assertIn("Pasal 2 (1) PMV menyelenggarakan Usaha Modal Ventura", answer["answer"])
        self.assertNotIn("DENGAN RAHMAT TUHAN YANG MAHA ESA", answer["answer"])
        self.assertNotIn("Menimbang", answer["answer"])

    def test_evidence_item_demotes_noisy_table_artifacts_unless_table_is_requested(self) -> None:
        base_row = {
            "_score": 100.0,
            "issuer": "OJK",
            "source": "peraturan-ojk",
            "source_priority": "primary",
            "file_role": "primary_regulation",
            "document_title": "Sistem Layanan Informasi Keuangan",
            "page_start": 4,
            "pasal": "Pasal 2",
            "citation_quality": "document_page_pasal",
        }
        clean = evidence_item(
            "apa kewajiban bank terkait pelaporan SLIK?",
            {
                **base_row,
                "section_type": "ayat",
                "text": "Bank wajib menyampaikan laporan debitur melalui Sistem Layanan Informasi Keuangan.",
            },
        )
        table = evidence_item(
            "apa kewajiban bank terkait pelaporan SLIK?",
            {
                **base_row,
                "section_type": "table",
                "text": "Bank wajib melapor | kolom | isi | |---|---|",
            },
        )
        requested_table = evidence_item(
            "tampilkan tabel kewajiban bank terkait pelaporan SLIK",
            {
                **base_row,
                "section_type": "table",
                "text": "Bank wajib melapor | kolom | isi | |---|---|",
            },
        )

        self.assertIn("markdown_table_artifact", table["extraction_flags"])
        self.assertLess(table["extraction_quality_multiplier"], clean["extraction_quality_multiplier"])
        self.assertLess(table["support_score"], clean["support_score"])
        self.assertEqual(requested_table["extraction_quality_multiplier"], 1.0)

    def test_answer_rank_prefers_obligation_clause_over_continuation_fragment(self) -> None:
        query = "apa kewajiban bank terkait pelaporan SLIK?"
        base = {
            "issuer": "OJK",
            "citation_quality": "document_page_pasal_ayat",
            "section_type": "ayat",
            "matched_exact_phrases": ["sistem layanan informasi keuangan"],
            "extraction_flags": [],
            "citation": {
                "document": "Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan",
                "page": 2,
                "pasal": "Pasal 2",
                "ayat": "(1)",
                "text": "Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan, hlm. 2, Pasal 2, ayat (1)",
            },
        }
        continuation = {
            **base,
            "support_score": 48.0,
            "text": "(1) bagi Debitur perseorangan fotokopi identitas diri dengan menunjukkan identitas diri asli.",
        }
        obligation = {
            **base,
            "support_score": 38.0,
            "text": "Sesuai dengan Pasal 2 ayat (1), pihak yang wajib menjadi Pelapor adalah Bank Umum, BPR, dan BPRS.",
        }

        self.assertGreater(answer_item_rank(query, obligation), answer_item_rank(query, continuation))
        self.assertFalse(is_usable_answer_claim(continuation["text"], continuation, query=query))
        self.assertTrue(is_usable_answer_claim(obligation["text"], obligation, query=query))

    def test_answer_claim_expands_incomplete_enumerator_from_neighbor_blocks(self) -> None:
        context_index = {
            "positions": {"block-1": [(("file-1", 4, "Pasal 2"), 0)]},
            "by_key": {
                ("file-1", 4, "Pasal 2"): [
                    {
                        "block_id": "block-1",
                        "block_type": "list_item",
                        "section_type": "ayat",
                        "text": "(1) Pihak yang wajib menjadi Pelapor meliputi:",
                    },
                    {
                        "block_id": "block-2",
                        "block_type": "table_or_row",
                        "section_type": "table",
                        "text": "| a. | Bank Umum; | |---|---| | b. | BPR; | | c. | BPRS; |",
                    },
                ]
            },
        }
        item = {
            "file_id": "file-1",
            "block_id": "block-1",
            "page_start": 4,
            "pasal": "Pasal 2",
            "text": "(1) Pihak yang wajib menjadi Pelapor meliputi:",
        }

        with patch("thinking_layer.answer.composer.source_context_index", return_value=context_index):
            claim = evidence_claim_text(item)

        self.assertIn("Pihak yang wajib menjadi Pelapor meliputi", claim)
        self.assertIn("Bank Umum", claim)
        self.assertIn("BPR", claim)
        self.assertIn("BPRS", claim)

    def test_context_join_respects_list_conjunctions(self) -> None:
        text = join_context_fragments(
            "Pihak yang wajib menjadi Pelapor adalah:",
            [
                "1) Bank Umum konvensional",
                "2) Bank Umum Syariah; dan",
                "3) Unit Usaha Syariah",
            ],
        )

        self.assertIn("2) Bank Umum Syariah; dan 3) Unit Usaha Syariah", text)
        self.assertNotIn("; dan; 3)", text)


if __name__ == "__main__":
    unittest.main()
