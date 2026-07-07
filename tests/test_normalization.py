from __future__ import annotations

import unittest

from thinking_layer.corpus.normalization import normalize_extracted_text, normalize_markdown_table_text


class NormalizationTests(unittest.TestCase):
    def test_markdown_table_enumerator_rows_become_readable_list(self) -> None:
        text = "| a. | Bank Umum; | |---|---| | b. | BPR; | | c. | BPRS; |"

        normalized = normalize_markdown_table_text(text)

        self.assertEqual(normalized, "a. Bank Umum; b. BPR; c. BPRS")
        self.assertNotIn("|---|", normalized)
        self.assertNotIn("|", normalized)

    def test_multiline_markdown_table_removes_separator_row(self) -> None:
        text = "\n".join(["| a. | Bank Umum |", "|---|---|", "| b. | BPR |"])

        normalized = normalize_extracted_text(text, "table_or_row")

        self.assertEqual(normalized, "a. Bank Umum; b. BPR")

    def test_wrapped_table_cells_are_joined_without_pipe_artifacts(self) -> None:
        text = "| d. | Lembaga | Pembiayaan Fasilitas Penyediaan Dana; | yang | memberikan |"

        normalized = normalize_extracted_text(text, "table_or_row")

        self.assertEqual(normalized, "d. Lembaga Pembiayaan Fasilitas Penyediaan Dana yang memberikan")

    def test_list_conjunction_punctuation_is_cleaned(self) -> None:
        text = "d. Lembaga Pembiayaan yang meliputi:; 1) Bank Umum konvensional; 2) Bank Umum Syariah; dan; 3) Unit Usaha Syariah"

        normalized = normalize_extracted_text(text, "paragraph")

        self.assertEqual(
            normalized,
            "d. Lembaga Pembiayaan yang meliputi: 1) Bank Umum konvensional; 2) Bank Umum Syariah; dan 3) Unit Usaha Syariah",
        )


if __name__ == "__main__":
    unittest.main()
