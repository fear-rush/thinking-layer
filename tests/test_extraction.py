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

    def test_extract_blocks_detects_word_ayat_and_huruf(self) -> None:
        manifest = {
            "canonical_id": "doc-1",
            "file_id": "file-1",
            "source": "peraturan-ojk",
            "issuer": "OJK",
            "file_role": "primary_regulation",
            "title": "POJK Contoh",
            "regulation_type": "POJK",
            "number": "1/2026",
            "year": "2026",
        }
        pages = [
            {
                "page_num": 4,
                "markdown": "\n".join(
                    [
                        "Pasal 9",
                        "Ketentuan Pasal 9 ayat 1 huruf a mengatur kewajiban pelaporan.",
                    ]
                ),
            }
        ]

        blocks = extract_blocks(manifest, pages)
        target = next(block for block in blocks if "kewajiban pelaporan" in block["text"])

        self.assertEqual(target["pasal"], "Pasal 9")
        self.assertEqual(target["ayat"], "(1)")
        self.assertEqual(target["huruf"], "huruf a")
        self.assertEqual(target["citation"]["huruf"], "huruf a")

    def test_extract_blocks_carries_ayat_to_huruf_list_items_only(self) -> None:
        manifest = {
            "canonical_id": "doc-1",
            "file_id": "file-1",
            "source": "peraturan-ojk",
            "issuer": "OJK",
            "file_role": "primary_regulation",
            "title": "POJK Contoh",
            "regulation_type": "POJK",
            "number": "1/2026",
            "year": "2026",
        }
        pages = [
            {
                "page_num": 5,
                "markdown": "\n".join(
                    [
                        "Pasal 10",
                        "(1) Bank wajib memenuhi persyaratan:",
                        "a. modal minimum;",
                        "b. tata kelola;",
                        "| a. | Bank Umum |",
                        "|---|---|",
                    ]
                ),
            }
        ]

        blocks = extract_blocks(manifest, pages)
        huruf_a = next(block for block in blocks if block["text"].startswith("a. modal"))
        huruf_b = next(block for block in blocks if block["text"].startswith("b. tata"))
        table = next(block for block in blocks if block["block_type"] == "table_or_row")

        self.assertEqual(huruf_a["pasal"], "Pasal 10")
        self.assertEqual(huruf_a["ayat"], "(1)")
        self.assertEqual(huruf_a["huruf"], "huruf a")
        self.assertEqual(huruf_b["ayat"], "(1)")
        self.assertEqual(huruf_b["huruf"], "huruf b")
        self.assertIsNone(table["ayat"])
        self.assertIsNone(table["huruf"])

    def test_extract_blocks_does_not_replace_context_with_mid_sentence_cross_reference(self) -> None:
        manifest = {
            "canonical_id": "doc-1",
            "file_id": "file-1",
            "source": "ease-bi",
            "issuer": "BI",
            "file_role": "primary_regulation",
            "title": "PBI Contoh",
            "regulation_type": "PBI",
            "number": "1/2026",
            "year": "2026",
        }
        pages = [
            {
                "page_num": 6,
                "markdown": "\n".join(
                    [
                        "Pasal 4",
                        "(2) Pemohon menyampaikan permohonan sebagaimana dimaksud dalam Pasal 3 huruf a dan huruf b.",
                    ]
                ),
            }
        ]

        blocks = extract_blocks(manifest, pages)
        target = next(block for block in blocks if "Pemohon menyampaikan" in block["text"])

        self.assertEqual(target["pasal"], "Pasal 4")
        self.assertEqual(target["ayat"], "(2)")
        self.assertIsNone(target["huruf"])

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

    def test_table_continuation_carries_header_for_xlsx_pages(self) -> None:
        manifest = {
            "canonical_id": "doc-1",
            "file_id": "file-1",
            "source": "ease-bi",
            "issuer": "BI",
            "file_role": "operational_requirement",
            "title": "Skenario Pengujian",
            "regulation_type": None,
            "number": None,
            "year": None,
            "resolved_path": "downloads/ease-bi/Skenario Functional Test.xlsx",
        }
        pages = [
            {
                "page_num": 2,
                "markdown": "\n".join(
                    [
                        "| No | Service | Scenario | Expected Result | Request |",
                        "|---|---|---|---|---|",
                        "| 1.1 | Any Service | Access Token Invalid | Error Code: 401xx01 | |",
                    ]
                ),
            },
            {
                "page_num": 3,
                "markdown": "\n".join(
                    [
                        "| 1.2 | Any Service | Unauthorized Signature | Error Code: 401xx00 | |",
                        "|---|---|---|---|---|",
                        "| 1.3 | Any Service | Invalid Format | Error Code: 400xx00 | |",
                    ]
                ),
            },
        ]

        blocks = [block for block in extract_blocks(manifest, pages) if block["block_type"] == "table_or_row"]

        self.assertEqual(len(blocks), 2)
        self.assertIsNone(blocks[0]["table_context"])
        self.assertEqual(blocks[1]["table_context"]["type"], "continued_table")
        self.assertEqual(blocks[1]["table_context"]["columns"], ["No", "Service", "Scenario", "Expected Result", "Request"])
        self.assertIn("Kolom tabel: No | Service | Scenario | Expected Result | Request.", blocks[1]["text"])
        self.assertIn("1.2 - Any Service - Unauthorized Signature", blocks[1]["text"])


if __name__ == "__main__":
    unittest.main()
