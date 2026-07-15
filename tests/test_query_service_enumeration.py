from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from thinking_layer.api.services.query_service import QueryService
from thinking_layer.corpus.citations import normalize_source_corpus_block
from thinking_layer.corpus.extraction import extract_blocks
from thinking_layer.indexing.lexical import build_search_index
from thinking_layer.indexing.sqlite import write_sqlite_search_index


class QueryServiceCanonicalEnumerationTests(unittest.TestCase):
    def test_service_carries_direct_enumeration_plan_to_a_canonical_pasal_two_leaf_citation(self) -> None:
        manifest = {
            "canonical_id": "bi-pjp-2021",
            "file_id": "bi-pjp-2021",
            "source": "ease-bi",
            "issuer": "BI",
            "file_role": "primary_regulation",
            "title": "PBI Penyedia Jasa Pembayaran",
            "regulation_type": "PBI",
            "number": "23/6/PBI/2021",
            "year": "2021",
            "lifecycle_status": "current",
            "is_current": True,
        }
        pages = [
            {
                "page_num": 4,
                "text": "\n".join(
                    [
                        "Pasal 2",
                        "(1) PJP menyelenggarakan aktivitas yang meliputi:",
                        "a. penyediaan informasi Sumber Dana;",
                        "b. inisiasi Pembayaran dan/atau akseptasi Instrumen Pembayaran.",
                        "(2) PJP dapat menyelenggarakan aktivitas lain setelah memperoleh persetujuan Bank Indonesia.",
                    ]
                ),
            }
        ]
        index = build_search_index(
            [
                normalize_source_corpus_block(block)
                for block in extract_blocks(manifest, pages)
            ]
        )

        with TemporaryDirectory() as directory:
            root = Path(directory)
            database_path = root / "search.sqlite"
            with (
                patch("thinking_layer.indexing.sqlite.SEARCH_INDEX_DIR", root),
                patch("thinking_layer.indexing.sqlite.SEARCH_INDEX_DB", database_path),
                patch("thinking_layer.retrieval.search.SEARCH_INDEX_DB", database_path),
                patch("thinking_layer.retrieval.evidence.sqlite_index_is_current", return_value=True),
                patch("thinking_layer.retrieval.search.sqlite_index_is_current", return_value=True),
            ):
                write_sqlite_search_index(index, filters={})
                execution = QueryService().answer("Apa aktivitas Penyedia Jasa Pembayaran?")

        plan_searches = execution.trace["query_plan"]["searches"]
        enumeration_searches = [
            search for search in plan_searches if search["reason"].startswith("direct_enumeration:")
        ]
        self.assertTrue(enumeration_searches)
        self.assertTrue(all("aktivitas" in search["query"] and "meliputi" in search["query"] for search in enumeration_searches))

        c1 = execution.answer["citations"][0]
        self.assertEqual((c1["pasal"], c1["ayat"], c1["huruf"]), ("Pasal 2", "(1)", None))
        self.assertEqual(c1["quality"], "document_page_pasal_ayat")
        self.assertEqual(len(c1["source_block_ids"]), 3)
        self.assertIn("huruf a penyediaan informasi Sumber Dana", c1["assembled_text"])
        self.assertIn("huruf b inisiasi Pembayaran", c1["assembled_text"])


if __name__ == "__main__":
    unittest.main()
