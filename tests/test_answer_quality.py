from __future__ import annotations

import unittest

from thinking_layer.answer.quality import evaluate_answer_quality


def structured_answer() -> dict[str, object]:
    return {
        "status": "answerable",
        "answer": "Ketentuan yang paling relevan ditemukan.",
        "summary": "Ketentuan yang paling relevan ditemukan.",
        "confidence": {"label": "strong", "score": 0.93, "reasons": []},
        "citation_count": 1,
        "documents_used": [
            {
                "issuer": "BI",
                "source_priority": "primary",
                "file_role": "primary_regulation",
            }
        ],
        "findings": [
            {
                "id": "f1",
                "text": "Penyedia Jasa Pembayaran wajib memperoleh persetujuan Bank Indonesia.",
                "citation_ids": ["c1"],
                "kind": "direct_rule",
                "status": "supported",
            }
        ],
        "citations": [
            {
                "id": "c1",
                "file_id": "bi-pjp",
                "block_id": "bi-pjp-4-2",
                "source_block_ids": ["bi-pjp-4-2", "bi-pjp-5-1"],
                "issuer": "BI",
                "text": "PBI Penyedia Jasa Pembayaran, hlm. 4–5, Pasal 2, ayat (1)",
                "page_start": 4,
                "page_end": 5,
            }
        ],
    }


class AnswerQualityTests(unittest.TestCase):
    def test_structured_answer_rewards_complete_supported_claim_with_exact_targets(self) -> None:
        result = evaluate_answer_quality(
            {
                "id": "v2-supported",
                "query": "apa ketentuan PJP?",
                "expected_behavior": "answerable",
                "required_issuers": ["BI"],
                "required_terms": ["Penyedia Jasa Pembayaran"],
                "required_citation_terms": ["hlm.", "Pasal"],
                "min_citations": 1,
            },
            structured_answer(),
        )

        self.assertTrue(result["accepted"])
        self.assertTrue(result["structured"])
        self.assertTrue(result["checks"]["findings_are_complete_and_supported"])
        self.assertTrue(result["checks"]["citation_targets_are_valid"])
        self.assertTrue(result["checks"]["no_orphan_citations"])

    def test_structured_answer_rejects_orphan_citation_and_incomplete_claim(self) -> None:
        answer = structured_answer()
        answer["findings"] = [
            {
                "id": "f1",
                "text": "Pihak yang wajib menjadi Pelapor meliputi:",
                "citation_ids": ["missing"],
                "kind": "direct_rule",
                "status": "supported",
            }
        ]
        result = evaluate_answer_quality(
            {"id": "v2-invalid", "query": "apa ketentuan PJP?", "expected_behavior": "answerable"}, answer
        )

        self.assertFalse(result["accepted"])
        self.assertFalse(result["checks"]["findings_are_complete_and_supported"])
        self.assertFalse(result["checks"]["no_orphan_citations"])

    def test_not_found_keeps_not_found_and_no_findings_gates(self) -> None:
        answer = {
            "status": "not_found",
            "answer": "Tidak ditemukan dalam dokumen yang tersedia.",
            "confidence": {"label": "weak", "score": 0.1, "reasons": []},
            "citation_count": 0,
            "findings": [],
            "citations": [],
            "documents_used": [],
        }
        result = evaluate_answer_quality(
            {
                "id": "not-found",
                "query": "aturan planet mars",
                "expected_behavior": "not_found",
                "required_terms": ["Tidak ditemukan"],
                "min_citations": 0,
            },
            answer,
        )

        self.assertTrue(result["accepted"])
        self.assertTrue(result["checks"]["not_found_has_no_findings"])


if __name__ == "__main__":
    unittest.main()
