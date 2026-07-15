from __future__ import annotations

import unittest

from thinking_layer.corpus.parser import parse_raw_document


class ParserBoundariesTest(unittest.TestCase):
    def test_preserves_article_and_nested_anchor_boundaries(self) -> None:
        parsed = parse_raw_document(
            {
                "file_id": "fixture-pbi-3-2023",
                "pages": [
                    {
                        "page_num": 1,
                        "markdown": (
                            "BAB I\nKETENTUAN UMUM\n\n"
                            "Pasal 1\n"
                            "(1) Istilah ini memiliki arti sebagai berikut.\n\n"
                            "(2) Ketentuan ini berlaku bagi bank.\n\n"
                            "Pasal 2\n"
                            "a. Bank wajib menyampaikan laporan.\n"
                        ),
                    }
                ],
            }
        )

        pasal_one = next(
            node
            for node in parsed.nodes
            if node.legal_path.pasal == "1" and node.node_kind == "pasal"
        )
        ayat_one = next(node for node in parsed.nodes if node.legal_path.ayat == "1")
        ayat_two = next(node for node in parsed.nodes if node.legal_path.ayat == "2")
        huruf_a = next(node for node in parsed.nodes if node.legal_path.huruf == "a")

        self.assertIn("Pasal 1", pasal_one.text)
        self.assertEqual(ayat_one.parent_node_id, pasal_one.node_id)
        self.assertEqual(ayat_two.parent_node_id, pasal_one.node_id)
        self.assertEqual(huruf_a.legal_path.pasal, "2")
        self.assertIn("Bank wajib menyampaikan laporan.", huruf_a.text)
        self.assertEqual(huruf_a.spans[0].page_start, 1)

    def test_keeps_a_cross_page_continuation_citable(self) -> None:
        parsed = parse_raw_document(
            {
                "file_id": "fixture-pojk-15-2025",
                "pages": [
                    {"page_num": 1, "markdown": "Pasal 5\nKetentuan dimulai pada halaman ini."},
                    {"page_num": 2, "markdown": "Ketentuan dilanjutkan pada halaman berikutnya."},
                ],
            }
        )

        continuation = next(node for node in parsed.nodes if node.node_kind == "continuation")
        self.assertEqual(continuation.legal_path.pasal, "5")
        self.assertEqual(
            continuation.parent_node_id,
            "fixture-pojk-15-2025:page:1:char:0:pasal",
        )
        self.assertIn("dilanjutkan", continuation.text)

    def test_splits_inline_ayat_boundaries_from_saved_markdown(self) -> None:
        parsed = parse_raw_document(
            {
                "file_id": "fixture-inline-ayat",
                "pages": [
                    {
                        "page_num": 1,
                        "markdown": "Pasal 1\n(1) Ketentuan pertama berlaku. (2) Ketentuan kedua berlaku.",
                    }
                ],
            }
        )

        ayat_one = next(node for node in parsed.nodes if node.legal_path.ayat == "1")
        ayat_two = next(node for node in parsed.nodes if node.legal_path.ayat == "2")
        self.assertIn("Ketentuan pertama berlaku.", ayat_one.text)
        self.assertNotIn("Ketentuan kedua", ayat_one.text)
        self.assertIn("Ketentuan kedua berlaku.", ayat_two.text)

    def test_keeps_lowercase_ayat_cross_references_in_the_same_clause(self) -> None:
        parsed = parse_raw_document(
            {
                "file_id": "fixture-ayat-reference",
                "pages": [
                    {
                        "page_num": 1,
                        "markdown": "Pasal 1\n(2) Layanan sebagaimana dimaksud pada\nayat (1) dikelola Bank Indonesia.",
                    }
                ],
            }
        )

        ayat = next(node for node in parsed.nodes if node.legal_path.ayat == "2")
        self.assertIn("dimaksud pada ayat (1) dikelola", ayat.retrieval_text)
        self.assertEqual(sum(node.node_kind == "ayat" for node in parsed.nodes), 1)


if __name__ == "__main__":
    unittest.main()
