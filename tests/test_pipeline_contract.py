from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from thinking_layer.api.services.documents import DocumentService
from thinking_layer.corpus.citations import normalize_source_corpus_block
from thinking_layer.corpus.extraction import extract_blocks
from thinking_layer.corpus.source_corpus import is_source_corpus_eligible
from thinking_layer.indexing.lexical import build_search_index
from thinking_layer.indexing.sqlite import sqlite_search, write_sqlite_search_index


def manifest() -> dict[str, object]:
    return {
        "canonical_id": "bi-pbi-1-2026",
        "file_id": "bi-pbi-1-2026",
        "source": "ease-bi",
        "issuer": "BI",
        "file_role": "primary_regulation",
        "title": "PBI Contoh",
        "regulation_type": "PBI",
        "number": "1/2026",
        "year": "2026",
        "lifecycle_status": "current",
        "is_current": True,
    }


def legal_block() -> dict[str, object]:
    return {
        "block_id": "node-angka-a",
        "node_id": "node-angka-a",
        "parent_id": "node-huruf-a",
        "previous_id": "node-angka-0",
        "document_part": "normative",
        "page_start": 4,
        "page_end": 5,
        "anchors": {"page_start": 4, "line_start": 8, "page_end": 5, "line_end": 3},
        "legal_path": {"bab": "BAB II", "pasal": "Pasal 2", "ayat": "(1)", "huruf": "huruf a", "angka": "1"},
        "display_text": "1. Penyedia wajib menyampaikan laporan.",
        "assembled_text": "1. Penyedia wajib menyampaikan laporan.",
        "retrieval_text": "BAB II Pasal 2 ayat (1) huruf a angka 1. Penyedia wajib menyampaikan laporan kepada Bank Indonesia.",
        "citation_admission": "atomic_leaf",
        "source_block_ids": ["node-angka-a"],
        "legal_unit": {
            "type": "angka",
            "label": "1",
            "document_part": "normative",
            "legal_path": {"bab": "BAB II", "pasal": "Pasal 2", "ayat": "(1)", "huruf": "huruf a", "angka": "1"},
            "parent_id": "node-huruf-a",
            "previous_id": "node-angka-0",
            "continuation": {
                "is_cross_page": True,
                "span_count": 2,
                "links": [{"span_id": "span-2", "continuation_of": "span-1"}],
            },
            "source_spans": [
                {"span_id": "span-1", "page": 4, "line_start": 8, "line_end": 20, "text": "1. Penyedia wajib"},
                {"span_id": "span-2", "page": 5, "line_start": 1, "line_end": 3, "text": "menyampaikan laporan.", "continuation_of": "span-1"},
            ],
            "display_source_id": "node-angka-a",
            "retrieval_source_id": "node-angka-a",
        },
        **manifest(),
        "document_title": "PBI Contoh",
    }


class CanonicalPipelineContractTests(unittest.TestCase):
    def test_canonical_normalization_keeps_legal_graph_and_separate_text_roles(self) -> None:
        row = normalize_source_corpus_block(legal_block())

        self.assertEqual(row["node_id"], "node-angka-a")
        self.assertEqual(row["parent_id"], "node-huruf-a")
        self.assertEqual(row["previous_id"], "node-angka-0")
        self.assertEqual(row["document_part"], "normative")
        self.assertEqual(row["legal_path"]["angka"], "1")
        self.assertEqual(row["unit_path"], ["BAB II", "Pasal 2", "(1)", "huruf a", "1"])
        self.assertEqual(row["text"], "1. Penyedia wajib menyampaikan laporan.")
        self.assertIn("Bank Indonesia", row["retrieval_text"])
        self.assertEqual(row["source_spans"][1]["page"], 5)
        self.assertTrue(row["continuation"]["is_cross_page"])
        self.assertEqual(row["citation"]["text"], "PBI Contoh, hlm. 4, Pasal 2, ayat (1), huruf a, angka 1")

    def test_source_corpus_admission_rejects_unmarked_canonical_parents(self) -> None:
        atomic_leaf = legal_block()
        aggregate = {
            **legal_block(),
            "block_id": "node-aggregate",
            "node_id": "node-aggregate",
            "unit_type": "enumeration_aggregate",
            "legal_unit_role": "enumeration_aggregate",
            "citation_admission": "enumeration_aggregate",
        }
        parent = {**legal_block(), "citation_admission": None}

        self.assertTrue(is_source_corpus_eligible(atomic_leaf))
        self.assertTrue(is_source_corpus_eligible(aggregate))
        self.assertFalse(is_source_corpus_eligible(parent))
        self.assertFalse(is_source_corpus_eligible({"block_id": "invalid", "text": "invalid"}))

    def test_legal_parser_indexes_atomic_leaves_and_bounded_enumeration_aggregates_only(self) -> None:
        pages = [
            {
                "page_num": 4,
                "text": "\n".join(
                    [
                        "BAB II Ketentuan",
                        "Pasal 2",
                        "(1) Penyedia wajib:",
                        "a. menyampaikan laporan;",
                        "1. kepada Bank Indonesia.",
                    ]
                ),
            }
        ]

        blocks = extract_blocks(manifest(), pages)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["unit_type"], "angka")
        self.assertEqual(blocks[0]["document_part"], "normative")
        self.assertEqual(blocks[0]["citation_admission"], "atomic_leaf")
        self.assertEqual(blocks[0]["file_id"], "bi-pbi-1-2026")
        self.assertEqual(blocks[0]["legal_path"]["pasal"], "Pasal 2")

    def test_lexical_sqlite_and_document_lookup_preserve_canonical_fields(self) -> None:
        row = normalize_source_corpus_block(legal_block())
        index = build_search_index([row])
        self.assertIn("indonesia", index.doc_terms[0])

        with TemporaryDirectory() as directory:
            root = Path(directory)
            database_path = root / "search.sqlite"
            with (
                patch("thinking_layer.indexing.sqlite.SEARCH_INDEX_DIR", root),
                patch("thinking_layer.indexing.sqlite.SEARCH_INDEX_DB", database_path),
            ):
                write_sqlite_search_index(index, filters={})
                hits = sqlite_search("Bank Indonesia", limit=1)
            self.assertEqual(hits[0]["legal_unit"]["type"], "angka")
            self.assertEqual(hits[0]["source_spans"][-1]["page"], 5)

            service = DocumentService(
                database_path,
                index_is_current=lambda: True,
            )
            response = service.get_block("bi-pbi-1-2026", "node-angka-a")

        self.assertEqual(response.text, "1. Penyedia wajib menyampaikan laporan.")
        self.assertEqual(response.legal_path["pasal"], "Pasal 2")
        self.assertEqual(response.source_spans[-1]["page"], 5)
        self.assertTrue(response.continuation["is_cross_page"])


if __name__ == "__main__":
    unittest.main()
