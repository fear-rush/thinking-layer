from __future__ import annotations

import unittest
from types import SimpleNamespace

from thinking_layer.corpus.extraction import extract_blocks, page_to_json, sentence_like_blocks


class ExtractionTests(unittest.TestCase):
    def test_sentence_blocks_preserve_markdown_table_as_own_block(self) -> None:
        text = "\n".join(
            [
                "Pasal 2",
                "(1) Bank wajib menyampaikan laporan.",
                "| a. | Bank Umum |",
                "|---|---|",
                "| b. | BPR |",
                "(2) Laporan disampaikan setiap bulan.",
            ]
        )

        blocks = sentence_like_blocks(text)

        self.assertIn("Pasal 2", blocks)
        self.assertIn("(1) Bank wajib menyampaikan laporan.", blocks)
        self.assertTrue(any("| a. | Bank Umum |" in block and "|---|---|" in block for block in blocks))
        self.assertIn("(2) Laporan disampaikan setiap bulan.", blocks)

    def test_extract_blocks_marks_table_without_merging_into_previous_ayat(self) -> None:
        manifest = {
            "canonical_id": "doc-1",
            "file_id": "file-1",
            "source": "peraturan-ojk",
            "issuer": "OJK",
            "file_role": "primary_regulation",
            "title": "POJK SLIK",
            "regulation_type": "POJK",
            "number": "1/2026",
            "year": "2026",
        }
        pages = [
            {
                "page_num": 2,
                "markdown": "\n".join(
                    [
                        "Pasal 2",
                        "(1) Bank wajib menyampaikan laporan.",
                        "| a. | Bank Umum |",
                        "|---|---|",
                        "| b. | BPR |",
                    ]
                ),
            }
        ]

        blocks = extract_blocks(manifest, pages)
        table_blocks = [block for block in blocks if block["block_type"] == "table_or_row"]
        ayat_blocks = [block for block in blocks if block["ayat"] == "(1)" and block["block_type"] != "table_or_row"]

        self.assertEqual(len(table_blocks), 1)
        self.assertEqual(table_blocks[0]["pasal"], "Pasal 2")
        self.assertEqual(table_blocks[0]["page_start"], 2)
        self.assertEqual(table_blocks[0]["text"], "a. Bank Umum; b. BPR")
        self.assertTrue(ayat_blocks)
        self.assertNotIn("|---|", ayat_blocks[0]["text"])

    def test_page_to_json_preserves_text_item_geometry_and_word_boxes(self) -> None:
        page = SimpleNamespace(
            page_num=1,
            width=100,
            height=200,
            text="Bank wajib melapor.",
            markdown="Bank wajib melapor.",
            text_items=[
                SimpleNamespace(
                    text="Bank wajib",
                    x=10,
                    y=20,
                    width=50,
                    height=12,
                    font_name="Arial",
                    font_size=10,
                    confidence=1.0,
                    rotation=0.0,
                    words=[
                        SimpleNamespace(text="Bank", x=10, y=20, width=20, height=12),
                        SimpleNamespace(text="wajib", x=32, y=20, width=28, height=12),
                    ],
                )
            ],
        )

        payload = page_to_json(page)

        self.assertEqual(payload["text_item_count"], 1)
        self.assertEqual(payload["text_items"][0]["x"], 10)
        self.assertEqual(payload["text_items"][0]["words"][1]["text"], "wajib")


if __name__ == "__main__":
    unittest.main()
