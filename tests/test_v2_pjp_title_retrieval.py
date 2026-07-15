from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from thinking_layer.corpus.citations import normalize_source_corpus_block
from thinking_layer.corpus.extraction import extract_blocks
from thinking_layer.indexing.lexical import build_search_index
from thinking_layer.indexing.sqlite import sqlite_search, sqlite_title_search, write_sqlite_search_index
from thinking_layer.retrieval.planning import build_query_plan
from thinking_layer.retrieval.search import execute_query_plan


class V2PjpTitleRetrievalTests(unittest.TestCase):
    def test_persisted_title_representative_prefers_the_pasal_two_ayat_one_aggregate(self) -> None:
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
        rows = [
            normalize_source_corpus_block(block)
            for block in extract_blocks(manifest, pages)
        ]
        index = build_search_index(rows)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            database_path = root / "search.sqlite"
            with (
                patch("thinking_layer.indexing.sqlite.SEARCH_INDEX_DIR", root),
                patch("thinking_layer.indexing.sqlite.SEARCH_INDEX_DB", database_path),
            ):
                write_sqlite_search_index(index, filters={})
                hits = sqlite_title_search(
                    "Penyedia Jasa Pembayaran",
                    limit=1,
                    issuer="BI",
                    role="primary_regulation",
                )
                plan = build_query_plan("Apa aktivitas Penyedia Jasa Pembayaran?")
                with (
                    patch("thinking_layer.retrieval.search.SEARCH_INDEX_DB", database_path),
                    patch("thinking_layer.retrieval.search.sqlite_index_is_current", return_value=True),
                ):
                    planned_hits = execute_query_plan(plan, limit=8)
                direct_enumeration_hits = sqlite_search(
                    plan["searches"][1]["query"],
                    limit=8,
                    issuer="BI",
                    role="primary_regulation",
                )
                subitem_hits = sqlite_search(
                    "PJP inisiasi Pembayaran",
                    limit=8,
                    issuer="BI",
                    role="primary_regulation",
                )

        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["citation"]["pasal"], "Pasal 2")
        self.assertEqual(hits[0]["citation"]["ayat"], "(1)")
        self.assertIsNone(hits[0]["citation"]["huruf"])
        self.assertEqual(hits[0]["legal_unit"]["role"], "enumeration_aggregate")
        self.assertEqual(len(hits[0]["source_block_ids"]), 3)
        self.assertIn("PJP menyelenggarakan aktivitas yang meliputi", hits[0]["retrieval_text"])

        enumeration_hits = [
            hit
            for hit in direct_enumeration_hits
            if hit["citation"]["pasal"] == "Pasal 2"
            and hit["citation"]["ayat"] == "(1)"
            and hit["legal_unit"].get("role") == "enumeration_aggregate"
        ]
        self.assertEqual(len(enumeration_hits), 1)
        hit = enumeration_hits[0]
        self.assertIn("PJP menyelenggarakan aktivitas yang meliputi", hit["retrieval_text"])
        self.assertIn("huruf a penyediaan informasi Sumber Dana", hit["display_text"])
        self.assertIn("huruf b inisiasi Pembayaran", hit["display_text"])
        self.assertIsNone(hit["citation"]["huruf"])
        self.assertEqual(hit["citation"]["quality"], "document_page_pasal_ayat")
        self.assertEqual(
            hit["citation"]["text"],
            "PBI Penyedia Jasa Pembayaran, hlm. 4, Pasal 2, ayat (1)",
        )
        self.assertTrue(
            any(
                row["citation"]["pasal"] == "Pasal 2"
                and row["citation"]["ayat"] == "(1)"
                and row["citation"]["huruf"] == "huruf b"
                for row in subitem_hits
            )
        )
        self.assertTrue(
            any(
                row["citation"]["pasal"] == "Pasal 2"
                and row["citation"]["ayat"] == "(1)"
                and row["legal_unit"].get("role") == "enumeration_aggregate"
                for row in planned_hits
            )
        )


if __name__ == "__main__":
    unittest.main()
