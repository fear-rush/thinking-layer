from __future__ import annotations

import importlib
import json
import sqlite3
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from thinking_layer.lexicon.merge import merge_generated_lexicon
from thinking_layer.indexing.lexical import append_search_index, build_search_index, index_signature, load_search_blocks
from thinking_layer.indexing.sqlite import incremental_build_index, sqlite_search, write_sqlite_search_index
from thinking_layer.indexing.semantic import _role_texts, cmd_semantic_search, semantic_model_settings, semantic_text
from thinking_layer.observability import trace_from_answer


def index_block(*, block_id: str, file_id: str, page: int, title: str, text: str) -> dict[str, object]:
    legal_path = {"pasal": "Pasal 1", "ayat": "(1)"}
    return {
        "block_id": block_id,
        "node_id": block_id,
        "file_id": file_id,
        "canonical_id": file_id,
        "issuer": "BI",
        "source": "ease-bi",
        "file_role": "primary_regulation",
        "document_title": title,
        "page_start": page,
        "page_end": page,
        "pasal": "Pasal 1",
        "ayat": "(1)",
        "legal_path": legal_path,
        "unit_path": ["Pasal 1", "(1)"],
        "display_text": text,
        "retrieval_text": text,
        "text": text,
        "source_block_ids": [block_id],
        "anchors": [{"page_start": page, "line_start": 1, "page_end": page, "line_end": 1}],
        "legal_unit": {"type": "ayat", "legal_path": legal_path, "source_spans": []},
        "citation_admission": "atomic_leaf",
    }


class ImportCliTests(unittest.TestCase):
    def test_core_modules_import_without_package_reexport_cycles(self) -> None:
        modules = [
            "thinking_layer.cli",
            "thinking_layer.corpus.build",
            "thinking_layer.corpus.parser_comparison",
            "thinking_layer.indexing.lexical",
            "thinking_layer.indexing.sqlite",
            "thinking_layer.indexing.semantic",
            "thinking_layer.retrieval.query_tools",
            "thinking_layer.retrieval.planning",
            "thinking_layer.retrieval.search",
            "thinking_layer.retrieval.evidence",
            "thinking_layer.answer.composer",
            "thinking_layer.answer.quality",
            "thinking_layer.observability",
            "thinking_layer.api.app",
            "thinking_layer.api.services.query_service",
            "thinking_layer.api.services.documents",
            "thinking_layer.evaluation.golden",
        ]

        for module_name in modules:
            with self.subTest(module=module_name):
                importlib.import_module(module_name)

    def test_cli_parser_exports_main(self) -> None:
        cli = importlib.import_module("thinking_layer.cli")

        self.assertTrue(callable(cli.main))

    def test_semantic_text_preserves_retrieval_context_and_limit(self) -> None:
        block = {
            **index_block(
                block_id="pjp-1",
                file_id="pjp",
                page=1,
                title="PBI Penyedia Jasa Pembayaran",
                text="Penyedia Jasa Pembayaran wajib memenuhi ketentuan.",
            ),
            "heading_path": ["BAB I", "Ketentuan Umum"],
            "number": "Pasal 1",
        }

        text = semantic_text(block, 80)

        self.assertIn("PBI Penyedia Jasa Pembayaran", text)
        self.assertIn("Pasal 1", text)
        self.assertEqual(len(text), 80)

    def test_semantic_model_settings_apply_e5_retrieval_prefixes(self) -> None:
        settings = semantic_model_settings("intfloat/multilingual-e5-small")

        self.assertEqual(settings["query_prefix"], "query: ")
        self.assertEqual(settings["document_prefix"], "passage: ")
        self.assertEqual(_role_texts("intfloat/multilingual-e5-small", "pertanyaan", "query"), "query: pertanyaan")
        self.assertEqual(_role_texts("intfloat/multilingual-e5-small", ["teks"], "document"), ["passage: teks"])

    def test_semantic_model_settings_keep_gte_custom_code_and_cpu_fallback_explicit(self) -> None:
        settings = semantic_model_settings("Alibaba-NLP/gte-multilingual-base")

        self.assertTrue(settings["trust_remote_code"])
        self.assertEqual(settings["device"], "cpu")
        self.assertEqual(settings["max_seq_length"], 8192)

    def test_semantic_cli_uses_configured_default_limit(self) -> None:
        args = Namespace(
            query="ketentuan pembayaran",
            limit=None,
            issuer=None,
            role=None,
            source=None,
            include_secondary=False,
        )
        with (
            patch("thinking_layer.indexing.semantic.semantic_config", return_value={"default_limit": 17}),
            patch("thinking_layer.indexing.semantic.semantic_search", return_value=[]) as search,
            patch("thinking_layer.indexing.lexical.format_search_results", return_value=""),
        ):
            cmd_semantic_search(args)

        search.assert_called_once_with(
            "ketentuan pembayaran",
            17,
            issuer=None,
            role=None,
            source=None,
            include_secondary=False,
        )

    def test_lexicon_merge_applies_approved_alias_updates_to_existing_topics(self) -> None:
        base = {"topics": [{"name": "consumer_protection", "patterns": ["perlindungan konsumen"]}]}
        reviewed = {
            "alias_updates": [
                {
                    "section": "topics",
                    "name": "consumer_protection",
                    "add_patterns": ["pelindungan konsumen"],
                    "approved": True,
                }
            ],
            "topics": [],
        }

        merged = merge_generated_lexicon(base, reviewed)

        self.assertEqual(merged["topics"][0]["patterns"], ["perlindungan konsumen", "pelindungan konsumen"])

    def test_query_trace_records_operational_decisions_and_retrieval_quality(self) -> None:
        answer = {
            "status": "not_found",
            "citation_count": 0,
            "composer": "template",
            "answer": "Tidak ditemukan dalam dokumen yang tersedia.\n",
            "documents_used": [],
            "evidence_pack": {
                "query": "aturan planet mars",
                "plan": {
                    "intents": ["find_regulations"],
                    "issuers": [None],
                    "entities": [],
                    "topics": [],
                    "searches": [{"query": "aturan planet mars", "reason": "raw_user_query"}],
                },
                "confidence": {
                    "label": "not_found",
                    "score": 0.1,
                    "must_say_not_found": True,
                    "reasons": ["no evidence retrieved"],
                },
                "documents": [],
                "ungrouped_evidence": [],
            },
        }

        trace = trace_from_answer(answer, generated_at="2026-07-11T00:00:00+00:00")

        self.assertEqual(trace["decision"]["status"], "not_found")
        self.assertTrue(trace["decision"]["refused"])
        self.assertEqual(trace["retrieval"]["evidence_count"], 0)
        self.assertEqual(trace["query_plan"]["search_count"], 1)

    def test_append_search_index_adds_only_new_documents_and_postings(self) -> None:
        first = index_block(
            block_id="first-1",
            file_id="first",
            page=1,
            title="PBI Pembayaran",
            text="Penyedia jasa pembayaran wajib memenuhi ketentuan.",
        )
        second = index_block(
            block_id="second-1",
            file_id="second",
            page=2,
            title="PBI Infrastruktur",
            text="Infrastruktur pembayaran wajib tersedia.",
        )

        index = build_search_index([first])
        append_search_index(index, [second])

        self.assertEqual(len(index.blocks), 2)
        self.assertEqual(index.postings["infrastruktur"], [1])
        self.assertEqual(index.postings["pembayaran"], [0, 1])

    def test_lexical_build_and_signature_require_source_corpus_even_when_blocks_exist(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "blocks.ndjson").write_text("{}\n", encoding="utf-8")
            with (
                patch("thinking_layer.indexing.lexical.PROCESSED_DIR", root),
                patch("thinking_layer.indexing.lexical.SOURCE_CORPUS_PATH", root / "missing-source.ndjson"),
            ):
                with self.assertRaisesRegex(SystemExit, "build-source-corpus"):
                    load_search_blocks(None, None, None, include_secondary=True)
                with self.assertRaisesRegex(FileNotFoundError, "build-source-corpus"):
                    index_signature()

    def test_incremental_sqlite_build_appends_without_json_companions(self) -> None:
        first = index_block(
            block_id="first-1",
            file_id="first",
            page=1,
            title="PBI Pembayaran",
            text="Penyedia jasa pembayaran wajib memenuhi ketentuan.",
        )
        second = index_block(
            block_id="second-1",
            file_id="second",
            page=2,
            title="PBI Infrastruktur",
            text="Infrastruktur pembayaran wajib tersedia.",
        )

        with TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source_corpus.ndjson"
            blocks_path = root / "blocks.ndjson"
            extracted_path = root / "extracted_documents.ndjson"
            search_dir = root / "search_index"
            database_path = search_dir / "search.sqlite"
            source_path.write_text(json.dumps(first) + "\n", encoding="utf-8")
            blocks_path.write_text(json.dumps(first) + "\n", encoding="utf-8")
            extracted_path.write_text("", encoding="utf-8")

            with (
                patch("thinking_layer.indexing.lexical.ROOT", root),
                patch("thinking_layer.indexing.lexical.PROCESSED_DIR", root),
                patch("thinking_layer.indexing.lexical.SOURCE_CORPUS_PATH", source_path),
                patch("thinking_layer.indexing.sqlite.ROOT", root),
                patch("thinking_layer.indexing.sqlite.SOURCE_CORPUS_PATH", source_path),
                patch("thinking_layer.indexing.sqlite.SEARCH_INDEX_DIR", search_dir),
                patch("thinking_layer.indexing.sqlite.SEARCH_INDEX_DB", database_path),
            ):
                write_sqlite_search_index(build_search_index([first]), filters={})
                with source_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(second) + "\n")

                updated, message = incremental_build_index({})
                hits = sqlite_search("infrastruktur", limit=1)

            conn = sqlite3.connect(database_path)
            try:
                document_count = conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
            finally:
                conn.close()

            self.assertTrue(updated)
            self.assertIn("appended 1", message)
            self.assertEqual(document_count, 2)
            self.assertEqual(hits[0]["block_id"], "second-1")
            self.assertEqual(list(search_dir.iterdir()), [database_path])

if __name__ == "__main__":
    unittest.main()
