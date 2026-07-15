from __future__ import annotations

import unittest

from thinking_layer.answer.composer import compose_template_answer
from thinking_layer.retrieval.topic_coverage import apply_cross_regulator_confidence_gate


class TopicCoverageTests(unittest.TestCase):
    def test_cross_regulator_adjacent_issuer_downgrades_to_partial(self) -> None:
        pack = {
            "query": "komparasi peraturan OJK dan BI terkait penyedia jasa pembayaran",
            "plan": {
                "raw_query": "komparasi peraturan OJK dan BI terkait penyedia jasa pembayaran",
                "intents": ["compare_regulations"],
                "issuers": ["OJK", "BI"],
                "entities": ["pjp"],
                "topics": ["payments"],
            },
            "confidence": {"label": "strong", "score": 1.0, "reasons": [], "must_say_not_found": False},
            "documents": [
                {
                    "issuer": "BI",
                    "document": "PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran",
                    "source_priority": "primary",
                    "file_role": "primary_regulation",
                    "citations": [
                        {
                            "file_id": "bi-pjp",
                            "block_id": "bi-pjp-1",
                            "source_block_ids": ["bi-pjp-1"],
                            "unit_path": ["Pasal 1"],
                            "legal_path": {"pasal": "Pasal 1"},
                            "anchors": [],
                            "source_spans": [],
                            "support_score": 30.0,
                            "score": 30.0,
                            "citation_quality": "document_page_pasal",
                            "section_type": "pasal",
                            "citation": {
                                "document": "PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran",
                                "page": 4,
                                "pasal": "Pasal 1",
                                "text": "PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 4, Pasal 1",
                            },
                            "snippet": "Pasal 1 Dalam Peraturan Bank Indonesia ini yang dimaksud dengan Penyedia Jasa Pembayaran adalah bank atau lembaga selain bank.",
                        }
                    ],
                },
                {
                    "issuer": "OJK",
                    "document": "Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto",
                    "source_priority": "primary",
                    "file_role": "primary_regulation",
                    "citations": [
                        {
                            "file_id": "ojk-akd-85-1",
                            "block_id": "ojk-akd-85-1",
                            "source_block_ids": ["ojk-akd-85-1"],
                            "unit_path": ["Pasal 85", "(1)"],
                            "legal_path": {"pasal": "Pasal 85", "ayat": "(1)"},
                            "anchors": [],
                            "source_spans": [],
                            "support_score": 25.0,
                            "score": 25.0,
                            "citation_quality": "document_page_pasal_ayat",
                            "section_type": "ayat",
                            "citation": {
                                "document": "Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto",
                                "page": 40,
                                "pasal": "Pasal 85",
                                "ayat": "(1)",
                                "text": "Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto, hlm. 40, Pasal 85, ayat (1)",
                            },
                            "snippet": "Transaksi dapat menggunakan penyedia jasa pembayaran yang telah memperoleh izin dari otoritas berwenang.",
                        }
                    ],
                },
            ],
            "ungrouped_evidence": [],
            "answer_policy": {},
        }

        gated = apply_cross_regulator_confidence_gate(pack)

        self.assertEqual(gated["confidence"]["label"], "partial")
        self.assertEqual(gated["topic_coverage"]["missing_direct_issuers"], ["OJK"])

        answer = compose_template_answer(gated, max_documents=4, max_citations_per_document=2)

        self.assertIn("issuer: OJK", answer["answer"])
        self.assertIn("PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran", answer["answer"])
        self.assertIn("konteks terkait, bukan bukti langsung", answer["answer"])
        self.assertNotIn("[1] OJK;", answer["answer"])


if __name__ == "__main__":
    unittest.main()
