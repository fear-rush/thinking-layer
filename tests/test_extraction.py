from __future__ import annotations

import unittest
from types import SimpleNamespace

from thinking_layer.corpus.extraction import extract_blocks, page_to_json
from thinking_layer.corpus.source_corpus import is_source_corpus_eligible


def manifest() -> dict[str, object]:
    return {
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


class ExtractionTests(unittest.TestCase):
    def test_seojk_outline_admits_only_bounded_explicit_leaf_paths(self) -> None:
        seojk_manifest = {
            **manifest(),
            "issuer": "OJK",
            "source": "peraturan-ojk",
            "title": "Pelaporan Debitur melalui SLIK",
            "regulation_type": "Surat Edaran OJK",
            "number": "11/SEOJK.01/2024",
        }
        pages = [
            {
                "page_num": 6,
                "text": "\n".join(
                    [
                        "IV. LAPORAN DEBITUR",
                        "7. Penyampaian Laporan Debitur dan/atau koreksi Laporan Debitur:",
                        "a. Penyampaian Laporan Secara Daring",
                        "1) Pelapor hanya dapat menyampaikan Laporan Debitur dan/atau koreksi Laporan Debitur oleh kantor pusat Pelapor secara daring kepada Otoritas Jasa Keuangan.",
                        "2) Sandi Pelapor yang digunakan dalam SLIK ditetapkan oleh Otoritas Jasa Keuangan.",
                    ]
                ),
            },
            {"page_num": 18, "text": "LAMPIRAN I\nSURAT EDARAN OTORITAS JASA KEUANGAN"},
            {
                "page_num": 28,
                "text": "\n".join(
                    [
                        "BAB I",
                        "B. Pelaporan Data Debitur melalui SLIK",
                        "1. Tujuan Pelaporan",
                        "a. Penyampaian Laporan Debitur dan/atau Koreksi Laporan Debitur",
                        "Dalam hal Pelapor menyampaikan laporan secara daring, secara bulanan paling lambat tanggal 12 berikutnya setelah bulan Laporan Debitur.",
                        "b. Penjelasan Umum Pelaporan",
                        "Pelapor menyusun data Debitur sesuai dengan pedoman pelaporan.",
                    ]
                ),
            },
        ]

        blocks = extract_blocks(seojk_manifest, pages)
        online = next(block for block in blocks if "hanya dapat menyampaikan" in block["display_text"])
        deadline = next(block for block in blocks if "paling lambat tanggal 12" in block["display_text"])

        self.assertEqual(online["citation_admission"], "atomic_leaf")
        self.assertEqual(
            online["legal_path"],
            {
                "section": "IV. LAPORAN DEBITUR",
                "point": "7",
                "subpoint": "a",
                "item": "1",
            },
        )
        self.assertEqual(deadline["citation_admission"], "atomic_leaf")
        self.assertEqual(deadline["document_part"], "attachment")
        self.assertEqual(deadline["legal_path"]["bab"], "BAB I")
        self.assertFalse(any(block.get("pasal") or block.get("ayat") or block.get("huruf") for block in (online, deadline)))
        self.assertTrue(is_source_corpus_eligible(online))
        self.assertTrue(is_source_corpus_eligible(deadline))

    def test_non_seojk_document_does_not_enable_outline_admission(self) -> None:
        blocks = extract_blocks(
            manifest(),
            [
                {
                    "page_num": 6,
                    "text": "IV. LAPORAN DEBITUR\n7. Penyampaian Laporan\na. Daring\n1) Laporan disampaikan secara daring.",
                }
            ],
        )

        self.assertEqual(blocks, [])

    def test_extract_blocks_emits_only_v2_atomic_leaves_and_bounded_aggregate(self) -> None:
        pages = [
            {
                "page_num": 4,
                # Raw text is intentionally in visual reading order even when
                # a companion Markdown conversion is not.
                "text": "\n".join(
                    [
                        "BAB II",
                        "Pasal 2",
                        "(1) PJP menyelenggarakan aktivitas yang meliputi:",
                        "a. penyediaan informasi Sumber Dana;",
                        "b. layanan remitansi.",
                    ]
                ),
                "markdown": "\n".join(
                    [
                        "(1) PJP menyelenggarakan aktivitas yang meliputi:",
                        "| a. | penyediaan informasi Sumber Dana; |",
                        "|---|---|",
                        "| b. | layanan remitansi. |",
                        "BAB II",
                        "Pasal 2",
                    ]
                ),
            }
        ]

        blocks = extract_blocks(manifest(), pages)
        atomic = [block for block in blocks if block["citation_admission"] == "atomic_leaf"]
        aggregates = [block for block in blocks if block["citation_admission"] == "enumeration_aggregate"]

        self.assertEqual(len(atomic), 2)
        self.assertEqual([block["huruf"] for block in atomic], ["huruf a", "huruf b"])
        self.assertEqual(len(aggregates), 1)
        self.assertTrue(all(block["chunk_schema_version"] == 2 for block in blocks))
        self.assertTrue(all(block["extraction_method"] == "legal_units_v2" for block in blocks))
        self.assertTrue(all(block["document_part"] == "normative" for block in blocks))
        self.assertTrue(all(block["legal_unit"]["document_part"] == "normative" for block in blocks))
        self.assertTrue(all(block["pasal"] == "Pasal 2" and block["ayat"] == "(1)" for block in blocks))
        self.assertIn("PJP menyelenggarakan aktivitas", aggregates[0]["display_text"])
        self.assertEqual(aggregates[0]["citation_target_id"], atomic[0]["parent_id"])

    def test_v2_table_leaf_retains_legal_owner_without_sentence_splitting(self) -> None:
        pages = [
            {
                "page_num": 2,
                "markdown": "\n".join(
                    [
                        "Pasal 2",
                        "(1) Bank wajib menyampaikan laporan:",
                        "| Huruf | Keterangan |",
                        "|---|---|",
                        "| a. | Bank Umum |",
                        "| b. | BPR |",
                    ]
                ),
            }
        ]

        blocks = extract_blocks(manifest(), pages)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["unit_type"], "table")
        self.assertEqual(blocks[0]["block_type"], "table_or_row")
        self.assertEqual(blocks[0]["pasal"], "Pasal 2")
        self.assertEqual(blocks[0]["ayat"], "(1)")
        self.assertIn("| a. | Bank Umum |", blocks[0]["display_text"])
        self.assertEqual(blocks[0]["table_readability"]["status"], "readable")
        self.assertTrue(is_source_corpus_eligible(blocks[0]))

    def test_formula_fragment_table_is_quarantined_from_citation_admission(self) -> None:
        pages = [
            {
                "page_num": 80,
                "markdown": "\n".join(
                    [
                        "Pasal 2",
                        "(1) Perhitungan mengikuti tabel:",
                        "| Komponen | Rumus |",
                        "|---|---|",
                        "| DRC | ∑ Wi × Li = DRC |",
                    ]
                ),
            }
        ]

        blocks = extract_blocks(manifest(), pages)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["citation_admission"], "quarantined_unreadable_table")
        self.assertIn("formula_dominant", blocks[0]["table_readability"]["reasons"])
        self.assertFalse(is_source_corpus_eligible(blocks[0]))

    def test_promulgation_and_dangling_reference_leaves_are_not_citation_evidence(self) -> None:
        promulgation = extract_blocks(
            manifest(),
            [{"page_num": 3, "text": "Pasal 2\nPeraturan ini berlaku.\nDitetapkan di Jakarta\n(1) Tanda tangan."}],
        )
        dangling = extract_blocks(
            manifest(),
            [{"page_num": 2, "text": "Pasal 1\n(1) Kewajiban sebagaimana dimaksud dalam Pasal"}],
        )

        self.assertTrue(any(block["citation_admission"] == "quarantined_non_evidence_document_part" for block in promulgation))
        self.assertEqual(dangling[0]["citation_admission"], "quarantined_dangling_legal_reference")
        self.assertFalse(any(is_source_corpus_eligible(block) for block in promulgation if block["document_part"] == "promulgation"))
        self.assertFalse(is_source_corpus_eligible(dangling[0]))

    def test_mojibake_table_is_quarantined_but_retained_for_audit(self) -> None:
        pages = [
            {
                "page_num": 87,
                "markdown": "\n".join(
                    [
                        "Pasal 3",
                        "(1) Parameter mengikuti tabel:",
                        "| Parameter | Nilai |",
                        "|---|---|",
                        "| Bobot risiko | â nilai eksposur |",
                    ]
                ),
            }
        ]

        blocks = extract_blocks(manifest(), pages)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["citation_quarantine"]["reason"], "unreadable_table")
        self.assertIn("mojibake", blocks[0]["table_readability"]["reasons"])
        self.assertFalse(is_source_corpus_eligible(blocks[0]))

    def test_page_to_json_preserves_raw_text_item_geometry_and_word_boxes(self) -> None:
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
