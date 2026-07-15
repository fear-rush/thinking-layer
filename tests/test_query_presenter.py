from __future__ import annotations

import unittest

from thinking_layer.api.presenters.queries import present_query
from thinking_layer.api.services.query_service import QueryExecution
from thinking_layer.retrieval.evidence import evidence_item


class QueryPresenterTests(unittest.TestCase):
    def test_evidence_carries_canonical_nested_legal_unit_provenance_to_the_composer(self) -> None:
        item = evidence_item(
            "apa ketentuan PJP?",
            {
                "_score": 10,
                "file_id": "bi-pjp",
                "block_id": "canonical-pjp-2-1",
                "document_title": "PBI Penyedia Jasa Pembayaran",
                "page_start": 4,
                "page_end": 5,
                "text": "Penyedia Jasa Pembayaran wajib memperoleh persetujuan.",
                "display_text": "Penyedia Jasa Pembayaran wajib memperoleh persetujuan.",
                "retrieval_text": "Pasal 2 ayat (1) Penyedia Jasa Pembayaran wajib memperoleh persetujuan.",
                "legal_path": {"pasal": "Pasal 2", "ayat": "(1)"},
                "unit_path": ["Pasal 2", "(1)"],
                "anchors": {"page_start": 4, "page_end": 5},
                "source_spans": [
                    {"span_id": "canonical-pjp-2-1:page-4:span-1", "page": 4, "line_start": 1, "line_end": 3}
                ],
                "source_block_ids": ["canonical-pjp-2-1"],
                "legal_unit": {
                    "type": "ayat",
                    "legal_path": {"pasal": "Pasal 2", "ayat": "(1)"},
                    "source_spans": [
                        {"span_id": "canonical-pjp-2-1:page-4:span-1", "page": 4, "line_start": 1, "line_end": 3}
                    ]
                },
            },
        )

        self.assertEqual(item["legal_path"], {"pasal": "Pasal 2", "ayat": "(1)"})
        self.assertEqual(item["anchors"]["page_end"], 5)
        self.assertEqual(item["source_spans"][0]["page"], 4)

    def test_preserves_canonical_legal_unit_provenance_in_the_public_contract(self) -> None:
        response = present_query(
            QueryExecution(
                request_id="request-canonical",
                duration_ms=5,
                trace={},
                answer={
                    "status": "answerable",
                    "answer": "Ketentuan ditemukan.",
                    "summary": "Ketentuan ditemukan.",
                    "confidence": {"label": "strong", "score": 0.9, "reasons": []},
                    "findings": [
                        {
                            "id": "f1",
                            "text": "Penyedia Jasa Pembayaran wajib memperoleh persetujuan.",
                            "citation_ids": ["c1"],
                            "kind": "direct_rule",
                            "status": "supported",
                        }
                    ],
                    "citations": [
                        {
                            "id": "c1",
                            "file_id": "bi-pjp",
                            "block_id": "canonical-pjp-2-1",
                            "source_block_ids": ["raw-pjp-4-2", "raw-pjp-5-1"],
                            "page": 4,
                            "page_start": 4,
                            "page_end": 5,
                            "unit_path": ["Pasal 2", "ayat (1)"],
                            "legal_path": {"pasal": "Pasal 2", "ayat": "(1)"},
                            "anchors": [{"page": 4, "label": "Pasal 2"}],
                            "source_spans": [{"block_id": "raw-pjp-4-2", "page_start": 4, "page_end": 4}],
                            "assembled_text": "Penyedia Jasa Pembayaran wajib memperoleh persetujuan Bank Indonesia.",
                        }
                    ],
                    "related_documents": [],
                    "limitations": [],
                },
            )
        )

        citation = response.citations[0]
        self.assertEqual(citation.source_block_ids, ["raw-pjp-4-2", "raw-pjp-5-1"])
        self.assertEqual((citation.page_start, citation.page_end), (4, 5))
        self.assertEqual(citation.unit_path, ["Pasal 2", "ayat (1)"])
        self.assertEqual(citation.legal_path, {"pasal": "Pasal 2", "ayat": "(1)"})
        self.assertEqual(citation.source_spans[0]["block_id"], "raw-pjp-4-2")

    def test_preserves_parser_anchor_list_for_the_public_contract(self) -> None:
        response = present_query(
            QueryExecution(
                request_id="request-canonical-anchor",
                duration_ms=1,
                trace={},
                answer={
                    "status": "answerable",
                    "answer": "Ketentuan ditemukan.",
                    "confidence": {"label": "strong", "score": 0.9, "reasons": []},
                    "citations": [
                        {
                            "id": "c1",
                            "file_id": "bi-pjp",
                            "block_id": "node-1",
                            "source_block_ids": ["node-1"],
                            "page": 4,
                            "page_start": 4,
                            "page_end": 5,
                            "unit_path": ["Pasal 2", "(1)"],
                            "legal_path": {"pasal": "Pasal 2", "ayat": "(1)"},
                            "anchors": [{"page_start": 4, "line_start": 8, "page_end": 5, "line_end": 3}],
                            "source_spans": [],
                        }
                    ],
                },
            )
        )

        self.assertEqual(
            response.citations[0].anchors,
            [{"page_start": 4, "line_start": 8, "page_end": 5, "line_end": 3}],
        )


if __name__ == "__main__":
    unittest.main()
