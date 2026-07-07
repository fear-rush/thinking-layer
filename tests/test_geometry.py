from __future__ import annotations

import unittest

from thinking_layer.corpus.geometry import geometry_text_for_block, reconstruct_indented_entries


def page_with_items() -> dict:
    return {
        "text_items": [
            {"text": "d.", "x": 226.97, "y": 791.69},
            {"text": "Lembaga", "x": 255.29, "y": 791.69},
            {"text": "Pembiayaan", "x": 328.00, "y": 791.69},
            {"text": "yang", "x": 419.34, "y": 791.69},
            {"text": "memberikan", "x": 467.52, "y": 791.69},
            {"text": "Fasilitas Penyediaan Dana;", "x": 255.29, "y": 805.73},
            {"text": "e.", "x": 226.97, "y": 819.89},
            {"text": "Perusahaan Efek yang menjalankan kegiatan", "x": 255.29, "y": 819.89},
            {"text": "usaha sebagai perantara pedagang efek;", "x": 255.29, "y": 833.93},
            {"text": "f.", "x": 226.97, "y": 848.09},
            {"text": "Lembaga Pendanaan Efek;", "x": 255.29, "y": 848.09},
            {"text": "https://jdih.ojk.go.id/", "x": 439.20, "y": 894.00},
        ]
    }


class GeometryTests(unittest.TestCase):
    def test_reconstruct_indented_entries_preserves_continuation_lines(self) -> None:
        entries = reconstruct_indented_entries(page_with_items())

        texts = [entry.text for entry in entries]
        self.assertIn("d. Lembaga Pembiayaan yang memberikan Fasilitas Penyediaan Dana", texts)
        self.assertIn("e. Perusahaan Efek yang menjalankan kegiatan usaha sebagai perantara pedagang efek", texts)
        self.assertIn("f. Lembaga Pendanaan Efek", texts)

    def test_geometry_text_for_block_matches_markdown_labels(self) -> None:
        block_text = "| d. | Lembaga | Pembiayaan | yang | memberikan | |---|---| | e. | Perusahaan Efek | | f. | Lembaga Pendanaan Efek |"

        text = geometry_text_for_block(block_text, page_with_items())

        self.assertEqual(
            text,
            "d. Lembaga Pembiayaan yang memberikan Fasilitas Penyediaan Dana; "
            "e. Perusahaan Efek yang menjalankan kegiatan usaha sebagai perantara pedagang efek; "
            "f. Lembaga Pendanaan Efek",
        )
        self.assertNotIn("https://", text)

    def test_geometry_text_requires_ordered_contiguous_label_sequence(self) -> None:
        page = {
            "text_items": [
                {"text": "b.", "x": 226.97, "y": 100.0},
                {"text": "koreksi Laporan Debitur", "x": 255.29, "y": 100.0},
                {"text": "1)", "x": 226.97, "y": 114.0},
                {"text": "Bank Umum konvensional", "x": 255.29, "y": 114.0},
                {"text": "b.", "x": 226.97, "y": 128.0},
                {"text": "Bank Perkreditan Rakyat (BPR);", "x": 255.29, "y": 128.0},
                {"text": "c.", "x": 226.97, "y": 142.0},
                {"text": "Bank Pembiayaan Rakyat Syariah (BPRS);", "x": 255.29, "y": 142.0},
                {"text": "d.", "x": 226.97, "y": 156.0},
                {"text": "Lembaga Pembiayaan yang meliputi:", "x": 255.29, "y": 156.0},
                {"text": "1)", "x": 226.97, "y": 170.0},
                {"text": "Lembaga Pembiayaan yang memberikan Fasilitas Penyediaan", "x": 255.29, "y": 170.0},
            ]
        }
        block_text = "| b. | Bank Perkreditan Rakyat | | c. | BPRS | | d. | Lembaga Pembiayaan | | 1) | Lembaga Pembiayaan |"

        text = geometry_text_for_block(block_text, page)

        self.assertIsNotNone(text)
        self.assertIn("b. Bank Perkreditan Rakyat", text or "")
        self.assertNotIn("koreksi Laporan Debitur", text or "")

    def test_reconstruct_indented_entries_accepts_slightly_indented_continuation(self) -> None:
        page = {
            "text_items": [
                {"text": "1)", "x": 153.26, "y": 476.16},
                {"text": "Lembaga Pembiayaan yang memberikan Fasilitas Penyediaan", "x": 171.26, "y": 476.16},
                {"text": "Dana; dan", "x": 171.26, "y": 497.28},
                {"text": "2)", "x": 153.26, "y": 518.52},
                {"text": "unit usaha syariah dari Lembaga Pembiayaan induknya; dan", "x": 171.26, "y": 518.52},
            ]
        }

        entries = reconstruct_indented_entries(page)

        self.assertEqual(
            entries[0].text,
            "1) Lembaga Pembiayaan yang memberikan Fasilitas Penyediaan Dana; dan",
        )


if __name__ == "__main__":
    unittest.main()
