from __future__ import annotations

import importlib
import unittest

from thinking_layer.evaluation.semantic import rrf_results, write_report
from thinking_layer.lexicon.merge import merge_generated_lexicon
from thinking_layer.indexing.lexical import append_search_index, build_search_index
from thinking_layer.indexing.semantic import _role_texts, semantic_model_settings, semantic_text
from thinking_layer.observability import trace_from_answer


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
            "thinking_layer.evaluation.evidence",
            "thinking_layer.evaluation.answer",
            "thinking_layer.evaluation.holdout",
            "thinking_layer.evaluation.natural",
            "thinking_layer.evaluation.semantic",
        ]

        for module_name in modules:
            with self.subTest(module=module_name):
                importlib.import_module(module_name)

    def test_cli_parser_exports_main(self) -> None:
        cli = importlib.import_module("thinking_layer.cli")

        self.assertTrue(callable(cli.main))

    def test_semantic_text_preserves_retrieval_context_and_limit(self) -> None:
        block = {
            "document_title": "PBI Penyedia Jasa Pembayaran",
            "heading_path": ["BAB I", "Ketentuan Umum"],
            "number": "Pasal 1",
            "pasal": "1",
            "ayat": "(1)",
            "text": "Penyedia Jasa Pembayaran wajib memenuhi ketentuan.",
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

    def test_semantic_report_can_record_model_failure(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        report = {
            "block_count": 5,
            "question_count": 1,
            "candidate_limit": 20,
            "rrf_k": 60,
            "bm25": {"summary": {"mrr": 1.0, "document_recall": {}, "issuer_coverage_at_10": 1.0}},
            "models": [{"model": "example/model", "status": "error", "error_type": "RuntimeError", "error": "unsupported runtime"}],
        }
        with TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            write_report(report, path)
            text = path.read_text(encoding="utf-8")

        self.assertIn("Status: `error`", text)
        self.assertIn("unsupported runtime", text)

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

        self.assertEqual(trace["schema_version"], 1)
        self.assertEqual(trace["decision"]["status"], "not_found")
        self.assertTrue(trace["decision"]["refused"])
        self.assertEqual(trace["retrieval"]["evidence_count"], 0)
        self.assertEqual(trace["query_plan"]["search_count"], 1)

    def test_append_search_index_adds_only_new_documents_and_postings(self) -> None:
        first = {
            "document_title": "PBI Pembayaran",
            "text": "Penyedia jasa pembayaran wajib memenuhi ketentuan.",
            "page_start": 1,
            "file_id": "first",
        }
        second = {
            "document_title": "PBI Infrastruktur",
            "text": "Infrastruktur pembayaran wajib tersedia.",
            "page_start": 2,
            "file_id": "second",
        }

        index = build_search_index([first])
        append_search_index(index, [second])

        self.assertEqual(len(index.blocks), 2)
        self.assertEqual(index.postings["infrastruktur"], [1])
        self.assertEqual(index.postings["pembayaran"], [0, 1])

    def test_rrf_fuses_ranked_lists_without_duplicate_blocks(self) -> None:
        lexical = [{"file_id": "a", "page_start": 1, "text": "same"}, {"file_id": "b", "page_start": 1, "text": "other"}]
        dense = [{"file_id": "a", "page_start": 1, "text": "same"}, {"file_id": "c", "page_start": 1, "text": "dense"}]

        results = rrf_results([lexical, dense], limit=3)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["file_id"], "a")
        self.assertEqual(results[0]["_retriever"], "rrf")


if __name__ == "__main__":
    unittest.main()
