from __future__ import annotations

import importlib
import unittest


class ImportCliTests(unittest.TestCase):
    def test_core_modules_import_without_package_reexport_cycles(self) -> None:
        modules = [
            "thinking_layer.cli",
            "thinking_layer.corpus.build",
            "thinking_layer.indexing.lexical",
            "thinking_layer.indexing.sqlite",
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
        ]

        for module_name in modules:
            with self.subTest(module=module_name):
                importlib.import_module(module_name)

    def test_cli_parser_exports_main(self) -> None:
        cli = importlib.import_module("thinking_layer.cli")

        self.assertTrue(callable(cli.main))


if __name__ == "__main__":
    unittest.main()
