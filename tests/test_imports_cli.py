from __future__ import annotations

import importlib
import unittest

from thinking_layer.evaluation.semantic import rrf_results
from thinking_layer.indexing.semantic import semantic_text


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

    def test_rrf_fuses_ranked_lists_without_duplicate_blocks(self) -> None:
        lexical = [{"file_id": "a", "page_start": 1, "text": "same"}, {"file_id": "b", "page_start": 1, "text": "other"}]
        dense = [{"file_id": "a", "page_start": 1, "text": "same"}, {"file_id": "c", "page_start": 1, "text": "dense"}]

        results = rrf_results([lexical, dense], limit=3)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["file_id"], "a")
        self.assertEqual(results[0]["_retriever"], "rrf")


if __name__ == "__main__":
    unittest.main()
