from __future__ import annotations

import unittest

from thinking_layer.corpus.legal_units import parse_legal_units


def unit_by_path(units: list[dict[str, object]], **path: str) -> dict[str, object]:
    return next(unit for unit in units if unit["legal_path"] == path)


class LegalUnitParserTests(unittest.TestCase):
    def test_normative_agar_clause_does_not_open_promulgation(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 6,
                    "text": "\n".join(
                        [
                            "Pasal 2",
                            "Agar pelaksanaan Transfer Dana berjalan aman, Penyelenggara wajib menerapkan prinsip kehati-hatian.",
                            "Pasal 3",
                            "Penyelenggara wajib menyampaikan pemberitahuan.",
                        ]
                    ),
                },
            ],
            document_id="normative-agar-fixture",
        )

        self.assertTrue(all(unit["document_part"] == "normative" for unit in units))
        self.assertIn("Agar pelaksanaan Transfer Dana", unit_by_path(units, pasal="Pasal 2")["display_text"])

    def test_outline_items_form_a_bounded_enumeration_aggregate(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 19,
                    "text": "\n".join(
                        [
                            "XIV. BATAS MAKSIMUM MANFAAT EKONOMI",
                            "3. Batas maksimum manfaat ekonomi terdiri atas:",
                            "b. Pendanaan konsumtif:",
                            "1) sebesar 0,3% per hari untuk tenor sampai dengan 6 bulan; dan",
                            "2) sebesar 0,2% per hari untuk tenor di atas 6 bulan.",
                        ]
                    ),
                },
                {
                    "page_num": 20,
                    "text": "2) Simulasi lanjutan yang mengulang label halaman sebelumnya. " + ("rincian " * 400),
                },
            ],
            document_id="outline-enumeration-fixture",
            enable_outline=True,
        )

        aggregate = next(
            unit
            for unit in units
            if unit.get("legal_unit_role") == "enumeration_aggregate"
            and unit["legal_path"].get("subpoint") == "b"
        )
        self.assertIn("0,3%", aggregate["display_text"])
        self.assertIn("0,2%", aggregate["display_text"])
        self.assertNotIn("Simulasi lanjutan", aggregate["display_text"])
        self.assertEqual(aggregate["legal_path"]["section"], "XIV. BATAS MAKSIMUM MANFAAT EKONOMI")

    def test_seojk_outline_uses_explicit_section_path_without_legal_anchor_invention(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 6,
                    "text": "\n".join(
                        [
                            "IV. LAPORAN DEBITUR",
                            "7. Penyampaian Laporan Debitur dan/atau koreksi Laporan Debitur:",
                            "a. Penyampaian Laporan Secara Daring",
                            "1) Pelapor hanya dapat menyampaikan Laporan Debitur dan/atau koreksi Laporan Debitur oleh kantor pusat Pelapor secara daring kepada Otoritas Jasa Keuangan.",
                            "2) Sandi Pelapor yang digunakan dalam SLIK ditetapkan oleh Otoritas Jasa Keuangan.",
                            "b. Penyampaian Laporan Secara Luring",
                            "1) Pelapor dapat menyampaikan laporan secara luring dalam hal mengalami gangguan teknis.",
                        ]
                    ),
                }
            ],
            document_id="seojk-slik-online-outline",
            enable_outline=True,
        )

        online = unit_by_path(
            units,
            section="IV. LAPORAN DEBITUR",
            point="7",
            subpoint="a",
            item="1",
        )

        self.assertEqual(online["unit_type"], "item")
        self.assertEqual(online["page_start"], 6)
        self.assertIn("secara daring kepada Otoritas Jasa Keuangan", online["display_text"])
        self.assertFalse(any(key in online["legal_path"] for key in ("pasal", "ayat", "huruf")))
        self.assertIn("IV. LAPORAN DEBITUR > 7 > a > 1", online["retrieval_text"])

    def test_seojk_attachment_outline_keeps_monthly_deadline_in_bounded_subpoint(self) -> None:
        units = parse_legal_units(
            [
                {"page_num": 18, "text": "LAMPIRAN I\nSURAT EDARAN OTORITAS JASA KEUANGAN"},
                {
                    "page_num": 20,
                    "text": "DAFTAR ISI\nBAB I Penjelasan Umum\nB. Pelaporan Data Debitur melalui SLIK - 7 -",
                },
                {
                    "page_num": 28,
                    "text": "\n".join(
                        [
                            "BAB I",
                            "B. Pelaporan Data Debitur melalui SLIK",
                            "1. Tujuan Pelaporan",
                            "a. Penyampaian Laporan Debitur dan/atau Koreksi Laporan Debitur",
                            "Dalam hal Pelapor menyampaikan Laporan Debitur dan/atau koreksi Laporan Debitur secara daring, secara bulanan paling lambat tanggal 12 berikutnya setelah bulan Laporan Debitur.",
                            "b. Penjelasan Umum Pelaporan",
                            "Pelapor SLIK menyusun data untuk Debitur yang memperoleh fasilitas.",
                        ]
                    ),
                },
            ],
            document_id="seojk-slik-monthly-outline",
            enable_outline=True,
        )

        deadline = unit_by_path(
            units,
            bab="BAB I",
            section="B. Pelaporan Data Debitur melalui SLIK",
            point="1",
            subpoint="a",
        )

        self.assertEqual(deadline["document_part"], "attachment")
        self.assertEqual(deadline["page_start"], deadline["page_end"])
        self.assertIn("paling lambat tanggal 12 berikutnya", deadline["display_text"])
        self.assertFalse(any(key in deadline["legal_path"] for key in ("pasal", "ayat", "huruf")))
        self.assertFalse(any(unit["page_start"] == 20 and unit["unit_type"] == "section" for unit in units))

    def test_pjp_page_four_uses_raw_reading_order_when_markdown_moves_pasal(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 3,
                    "text": "\n".join(
                        [
                            "BAB I",
                            "Pasal 1",
                            "(1) Penyedia Jasa Pembayaran yang selanjutnya disingkat PJP adalah Bank atau Lembaga Selain Bank.",
                        ]
                    ),
                },
                {
                    "page_num": 4,
                    "text": "\n".join(
                        [
                            "BAB II",
                            "Pasal 2",
                            "(1) PJP menyelenggarakan aktivitas yang meliputi:",
                            "a. penyediaan informasi Sumber Dana;",
                            "b. layanan remitansi.",
                        ]
                    ),
                    # This is the known malformed visual order.  The raw text
                    # above is the supplied ordered source and must win.
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
            ],
            document_id="ease-bi-pbi-23-6-2021",
        )

        ayat = unit_by_path(
            units,
            bab="BAB II",
            pasal="Pasal 2",
            ayat="(1)",
        )
        huruf = [unit for unit in units if unit["unit_type"] == "huruf"]
        aggregates = [unit for unit in units if unit.get("legal_unit_role") == "enumeration_aggregate"]

        self.assertEqual(ayat["display_text"], "(1) PJP menyelenggarakan aktivitas yang meliputi:")
        self.assertEqual([unit["legal_path"]["huruf"] for unit in huruf], ["huruf a", "huruf b"])
        self.assertTrue(all(unit["legal_path"]["pasal"] == "Pasal 2" for unit in huruf))
        self.assertEqual(huruf[1]["previous_id"], huruf[0]["node_id"])
        # The citation remains the exact list child, while retrieval gets only
        # the governing Ayat subject.  Sibling list content must not leak in.
        self.assertEqual(huruf[0]["display_text"], "huruf a penyediaan informasi Sumber Dana;")
        self.assertNotIn("PJP menyelenggarakan", huruf[0]["display_text"])
        self.assertIn("PJP menyelenggarakan aktivitas yang meliputi", huruf[0]["retrieval_text"])
        self.assertIn("penyediaan informasi Sumber Dana", huruf[0]["retrieval_text"])
        self.assertIn("Penyedia Jasa Pembayaran (PJP)", huruf[0]["retrieval_text"])
        self.assertEqual(
            huruf[0]["retrieval_aliases"],
            [{"alias": "PJP", "full_form": "Penyedia Jasa Pembayaran"}],
        )
        self.assertNotIn("layanan remitansi", huruf[0]["retrieval_text"])
        self.assertNotIn("BAB II", huruf[0]["retrieval_text"])
        self.assertEqual(len(aggregates), 1)
        aggregate = aggregates[0]
        self.assertEqual(aggregate["parent_id"], ayat["node_id"])
        self.assertEqual(aggregate["citation_target_id"], ayat["node_id"])
        self.assertEqual(aggregate["legal_path"], ayat["legal_path"])
        self.assertIn("PJP menyelenggarakan aktivitas yang meliputi", aggregate["display_text"])
        self.assertIn("huruf a penyediaan informasi Sumber Dana", aggregate["display_text"])
        self.assertIn("huruf b layanan remitansi", aggregate["display_text"])
        self.assertIn("Penyedia Jasa Pembayaran (PJP)", aggregate["retrieval_text"])
        self.assertEqual(aggregate["source_block_ids"], [ayat["node_id"], *(item["node_id"] for item in huruf)])

    def test_pjp_definition_continues_across_pages_as_one_ayat_with_linked_spans(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 3,
                    "text": "\n".join(
                        [
                            "BAB I",
                            "Pasal 1",
                            "(1) Penyedia Jasa Pembayaran yang selanjutnya disingkat PJP adalah",
                        ]
                    ),
                },
                {
                    "page_num": 4,
                    "text": "pihak yang menyediakan jasa untuk memfasilitasi transaksi pembayaran kepada Pengguna Jasa.",
                },
            ],
            document_id="ease-bi-pbi-23-6-2021",
        )

        ayat = unit_by_path(units, bab="BAB I", pasal="Pasal 1", ayat="(1)")
        spans = ayat["legal_unit"]["source_spans"]

        self.assertEqual(ayat["page_start"], 3)
        self.assertEqual(ayat["page_end"], 4)
        self.assertIn("adalah pihak yang menyediakan", ayat["display_text"])
        self.assertEqual([span["page"] for span in spans], [3, 4])
        self.assertEqual(spans[1]["continuation_of"], spans[0]["span_id"])
        self.assertTrue(ayat["legal_unit"]["continuation"]["is_cross_page"])
        self.assertEqual(ayat["source_block_ids"], [ayat["node_id"]])

    def test_split_pasal_three_clause_is_not_emitted_as_orphan_continuation_chunk(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 5,
                    "text": "\n".join(
                        [
                            "Pasal 3",
                            "(1) PJP wajib memastikan keamanan sistem dan data",
                        ]
                    ),
                },
                {
                    "page_num": 6,
                    "text": "dalam penyelenggaraan aktivitasnya secara berkelanjutan.",
                },
            ],
            document_id="pbi-split-clause",
        )

        ayats = [unit for unit in units if unit["unit_type"] == "ayat"]

        self.assertEqual(len(ayats), 1)
        self.assertEqual(ayats[0]["legal_path"], {"pasal": "Pasal 3", "ayat": "(1)"})
        self.assertIn("data dalam penyelenggaraan", ayats[0]["display_text"])
        self.assertEqual(ayats[0]["anchors"]["page_end"], 6)

    def test_pbi_3_2023_wrapped_ayat_reference_does_not_create_false_ayat(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 15,
                    "text": "\n".join(
                        [
                            "Pasal 39",
                            "(1) Penyelenggara wajib memiliki fungsi yang menangani pengaduan.",
                            "(2) Dalam menangani pengaduan sebagaimana dimaksud pada",
                            "ayat (1), pihak lainnya yang diatur dan diawasi oleh Bank Indonesia wajib bersama-sama Penyelenggara menyelesaikan pengaduan Konsumen.",
                            "(3) Penyelenggara wajib menindaklanjuti hasil penyelesaian.",
                        ]
                    ),
                }
            ],
            document_id="ease-bi-ketentuan-1293-pbi-3-2023",
        )

        ayats = [unit for unit in units if unit["unit_type"] == "ayat"]
        ayat_two = unit_by_path(units, pasal="Pasal 39", ayat="(2)")

        self.assertEqual([unit["legal_path"]["ayat"] for unit in ayats], ["(1)", "(2)", "(3)"])
        self.assertIn("dimaksud pada ayat (1), pihak lainnya", ayat_two["display_text"])

    def test_pbi_10_2024_wrapped_reference_suffix_stays_in_ayat_one(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 17,
                    "text": "\n".join(
                        [
                            "Pasal 24",
                            "(1) Identifikasi sebagaimana dimaksud dalam Pasal 16 ayat",
                            "(1) huruf a dan verifikasi sebagaimana dimaksud dalam Pasal 16 ayat (1) huruf b tidak diharuskan bagi Penyelenggara tertentu.",
                            "(2) Bank Indonesia dapat menetapkan kebijakan yang berbeda.",
                        ]
                    ),
                }
            ],
            document_id="ease-bi-ketentuan-1294-pbi-10-2024",
        )

        ayats = [unit for unit in units if unit["unit_type"] == "ayat"]
        ayat_one = unit_by_path(units, pasal="Pasal 24", ayat="(1)")

        self.assertEqual([unit["legal_path"]["ayat"] for unit in ayats], ["(1)", "(2)"])
        self.assertIn("Pasal 16 ayat (1) huruf a", ayat_one["display_text"])

    def test_reference_shaped_continuation_across_page_boundary_keeps_linked_spans(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 17,
                    "text": "Pasal 24\n(1) Identifikasi sebagaimana dimaksud dalam Pasal 16 ayat",
                },
                {
                    "page_num": 18,
                    "text": "(1) huruf a wajib dilakukan sebelum hubungan usaha dimulai.\n(2) Bank Indonesia dapat menetapkan kebijakan lain.",
                },
            ],
            document_id="cross-page-reference-fixture",
        )

        ayat_one = unit_by_path(units, pasal="Pasal 24", ayat="(1)")
        spans = ayat_one["legal_unit"]["source_spans"]

        self.assertEqual(ayat_one["page_start"], 17)
        self.assertEqual(ayat_one["page_end"], 18)
        self.assertEqual([span["page"] for span in spans], [17, 18])
        self.assertEqual(spans[1]["continuation_of"], spans[0]["span_id"])
        self.assertTrue(ayat_one["legal_unit"]["continuation"]["is_cross_page"])
        self.assertEqual(
            [unit["legal_path"]["ayat"] for unit in units if unit["unit_type"] == "ayat"],
            ["(1)", "(2)"],
        )

    def test_pojk_6_2022_wrapped_reference_does_not_replace_ayat_seven(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 10,
                    "text": "\n".join(
                        [
                            "Pasal 11",
                            "(7) Penarikan persetujuan pemberian data pribadi sebagaimana dimaksud pada ayat",
                            "(3) huruf a dilakukan secara tertulis atau elektronik oleh Konsumen.",
                            "Pasal 12",
                            "(1) PUJK wajib melakukan perancangan produk.",
                        ]
                    ),
                }
            ],
            document_id="peraturan-ojk-pojk-6-07-2022",
        )

        ayat_seven = unit_by_path(units, pasal="Pasal 11", ayat="(7)")

        self.assertIn("ayat (3) huruf a dilakukan", ayat_seven["display_text"])
        self.assertFalse(
            any(
                unit["legal_path"] == {"pasal": "Pasal 11", "ayat": "(3)"}
                for unit in units
            )
        )

    def test_pojk_wrapped_ayat_reference_with_terminal_period_is_not_a_sibling(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 36,
                    "text": "\n".join(
                        [
                            "Pasal 58",
                            "(4) Otoritas Jasa Keuangan dapat meminta Bank melakukan penyesuaian sebagaimana dimaksud pada",
                            "ayat (2).",
                            "Pasal 59",
                            "Bank wajib melaporkan kondisi terkini penyelenggaraan TI.",
                        ]
                    ),
                }
            ],
            document_id="pojk-wrapped-ayat-period",
        )

        ayat_four = unit_by_path(units, pasal="Pasal 58", ayat="(4)")

        self.assertIn("dimaksud pada ayat (2).", ayat_four["display_text"])
        self.assertEqual(
            [
                unit["legal_path"]["ayat"]
                for unit in units
                if unit["unit_type"] == "ayat"
                and unit["legal_path"].get("pasal") == "Pasal 58"
            ],
            ["(4)"],
        )

    def test_pojk_wrapped_huruf_reference_after_conjunction_is_not_a_child(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 37,
                    "text": "\n".join(
                        [
                            "Pasal 60",
                            "(5) Bank dianggap telah memenuhi ketentuan sebagaimana dimaksud pada ayat (1) huruf a dan/atau",
                            "huruf b.",
                            "Pasal 61",
                            "(1) Bank wajib menyampaikan laporan realisasi.",
                        ]
                    ),
                }
            ],
            document_id="pojk-wrapped-huruf-conjunction",
        )

        ayat_five = unit_by_path(units, pasal="Pasal 60", ayat="(5)")

        self.assertIn("huruf a dan/atau huruf b.", ayat_five["display_text"])
        self.assertFalse(
            any(
                unit["unit_type"] == "huruf"
                and unit["legal_path"].get("pasal") == "Pasal 60"
                and unit["legal_path"].get("ayat") == "(5)"
                for unit in units
            )
        )

    def test_complete_pasal_and_ayat_reference_tails_keep_wrapped_suffixes(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 15,
                    "text": "\n".join(
                        [
                            "Pasal 24",
                            "(1) Pengujian keamanan siber sebagaimana dimaksud dalam Pasal 23",
                            "huruf a wajib dilaksanakan secara berkala.",
                            "(2) Notifikasi awal sebagaimana dimaksud pada ayat (1)",
                            "huruf a disampaikan secara elektronik.",
                            "(3) Sistem komunikasi sebagaimana dimaksud pada ayat (2)",
                            "huruf d harus didukung teknologi.",
                        ]
                    ),
                }
            ],
            document_id="pojk-complete-reference-tails",
        )

        self.assertIn(
            "Pasal 23 huruf a wajib dilaksanakan",
            unit_by_path(units, pasal="Pasal 24", ayat="(1)")["display_text"],
        )
        self.assertIn(
            "ayat (1) huruf a disampaikan",
            unit_by_path(units, pasal="Pasal 24", ayat="(2)")["display_text"],
        )
        self.assertIn(
            "ayat (2) huruf d harus didukung",
            unit_by_path(units, pasal="Pasal 24", ayat="(3)")["display_text"],
        )
        self.assertFalse(any(unit["unit_type"] == "huruf" for unit in units))

    def test_wrapped_pasal_and_ayat_reference_lists_do_not_open_new_units(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 11,
                    "text": "\n".join(
                        [
                            "Pasal 14",
                            "(1) Ketentuan berlaku sebagaimana dimaksud dalam Pasal 12",
                            "ayat (1), dan/atau Pasal 13 ayat (1).",
                            "(2) Pelanggaran Pasal 11 ayat (1),",
                            "ayat (4), Pasal 12 ayat (1), dan/atau",
                            "Pasal 13 ayat (1), dikenai sanksi administratif berupa:",
                            "a. larangan kegiatan tertentu; dan",
                            "b. teguran tertulis.",
                            "Pasal 15",
                            "(1) Bank wajib menerapkan manajemen risiko.",
                        ]
                    ),
                }
            ],
            document_id="pojk-wrapped-reference-lists",
        )

        ayat_one = unit_by_path(units, pasal="Pasal 14", ayat="(1)")
        ayat_two = unit_by_path(units, pasal="Pasal 14", ayat="(2)")

        self.assertIn("Pasal 12 ayat (1), dan/atau Pasal 13", ayat_one["display_text"])
        self.assertIn("ayat (4), Pasal 12", ayat_two["display_text"])
        self.assertIn("Pasal 13 ayat (1), dikenai", ayat_two["display_text"])
        self.assertEqual(
            [
                unit["legal_path"]["pasal"]
                for unit in units
                if unit["unit_type"] == "pasal"
            ],
            ["Pasal 14", "Pasal 15"],
        )
        self.assertEqual(
            [
                unit["legal_path"]["ayat"]
                for unit in units
                if unit["unit_type"] == "ayat"
                and unit["legal_path"].get("pasal") == "Pasal 14"
            ],
            ["(1)", "(2)"],
        )
        self.assertEqual(
            [
                unit["legal_path"]["huruf"]
                for unit in units
                if unit["unit_type"] == "huruf"
            ],
            ["huruf a", "huruf b"],
        )

    def test_true_pasal_and_ayat_headings_still_open_distinct_units(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 40,
                    "text": "\n".join(
                        [
                            "Pasal 70",
                            "(1) Bank wajib menyimpan laporan.",
                            "(2) Bank wajib memperbarui laporan.",
                            "Pasal 71",
                            "(1) Ketentuan mulai berlaku.",
                        ]
                    ),
                }
            ],
            document_id="true-heading-negative-control",
        )

        self.assertEqual(
            [unit["legal_path"]["pasal"] for unit in units if unit["unit_type"] == "pasal"],
            ["Pasal 70", "Pasal 71"],
        )
        self.assertEqual(
            [
                unit["legal_path"]["ayat"]
                for unit in units
                if unit["unit_type"] == "ayat"
                and unit["legal_path"].get("pasal") == "Pasal 70"
            ],
            ["(1)", "(2)"],
        )

    def test_pbi_22_23_terminal_pasal_stops_before_promulgation_and_explanation(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 49,
                    "text": "Pasal 122\nPeraturan Bank Indonesia ini mulai berlaku pada tanggal 1 Juli 2021.",
                },
                {
                    "page_num": 50,
                    "text": "\n".join(
                        [
                            "Agar setiap orang mengetahuinya, memerintahkan pengundangan Peraturan Bank Indonesia ini dengan penempatannya dalam Lembaran Negara Republik Indonesia.",
                            "Ditetapkan di Jakarta",
                            "pada tanggal 29 Desember 2020",
                            "GUBERNUR BANK INDONESIA,",
                        ]
                    ),
                },
                {
                    "page_num": 51,
                    "text": "PENJELASAN\nATAS\nPERATURAN BANK INDONESIA\nNOMOR 22/23/PBI/2020",
                },
                {
                    "page_num": 53,
                    "text": "II. PASAL DEMI PASAL\nPasal 1\nCukup jelas.",
                },
            ],
            document_id="ease-bi-ketentuan-1132-pbi-22-23-2020",
        )

        terminal = unit_by_path(units, pasal="Pasal 122")
        explanation = unit_by_path(units, pasal="Pasal 1")

        self.assertEqual(terminal["page_end"], 49)
        self.assertEqual(terminal["document_part"], "normative")
        self.assertNotIn("Agar setiap orang", terminal["display_text"])
        self.assertNotIn("PENJELASAN", terminal["display_text"])
        self.assertEqual(explanation["document_part"], "explanation")
        self.assertEqual(explanation["legal_unit"]["document_part"], "explanation")

    def test_ojk_footer_url_is_removed_from_legal_evidence_text(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 8,
                    "text": "Pasal 7\n(1) Penyelenggara wajib memiliki modal disetor paling sedikit Rp25.000.000.000,00. https://jdih.ojk.go.id/",
                }
            ],
            document_id="pojk-40-2024",
        )

        ayat = unit_by_path(units, pasal="Pasal 7", ayat="(1)")

        self.assertNotIn("jdih.ojk.go.id", ayat["display_text"])
        self.assertNotIn("jdih.ojk.go.id", ayat["retrieval_text"])
        self.assertNotIn("jdih.ojk.go.id", ayat["legal_unit"]["source_spans"][0]["text"])

    def test_true_markdown_table_is_a_child_table_not_fabricated_huruf(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 9,
                    "markdown": "\n".join(
                        [
                            "Pasal 7",
                            "(1) Kewajiban pelaporan mengikuti tabel berikut:",
                            "| Huruf | Kewajiban |",
                            "|---|---|",
                            "| a. | Laporan harian |",
                            "| b. | Laporan bulanan |",
                        ]
                    ),
                }
            ],
            document_id="pbi-true-table",
        )

        ayat = unit_by_path(units, pasal="Pasal 7", ayat="(1)")
        tables = [unit for unit in units if unit["unit_type"] == "table"]

        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]["parent_id"], ayat["node_id"])
        self.assertIn("| a. | Laporan harian |", tables[0]["display_text"])
        self.assertIn("Pasal 7 > (1) Tabel", tables[0]["retrieval_text"])
        self.assertFalse(any(unit["unit_type"] == "huruf" for unit in units))

    def test_aliases_require_explicit_unambiguous_uppercase_definitions(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 1,
                    "text": "\n".join(
                        [
                            "Pasal 1",
                            "(1) Sumber Dana yang selanjutnya disebut Sumber Dana adalah dana untuk pembayaran.",
                            "(2) Penyedia Jasa Pembayaran yang selanjutnya disingkat PJP adalah Bank.",
                            "(3) Pihak Jasa Pembayaran yang selanjutnya disingkat PJP adalah Lembaga.",
                            "Pasal 2",
                            "(1) PJP wajib menyampaikan laporan.",
                            "a. laporan berkala.",
                        ]
                    ),
                }
            ],
            document_id="ambiguous-alias-fixture",
        )

        child = unit_by_path(units, pasal="Pasal 2", ayat="(1)", huruf="huruf a")

        # A title-cased defined term is not an acronym, and an acronym with two
        # different full forms is not safe to expand document-wide.
        self.assertEqual(child["retrieval_aliases"], [])
        self.assertNotIn("Istilah terkait:", child["retrieval_text"])
        self.assertEqual(child["display_text"], "huruf a laporan berkala.")
        self.assertFalse(any(unit.get("legal_unit_role") == "enumeration_aggregate" for unit in units))

    def test_enumeration_aggregate_is_bounded_to_twelve_immediate_children(self) -> None:
        items = [f"{letter}. kewajiban {index};" for index, letter in enumerate("abcdefghijklm", start=1)]
        units = parse_legal_units(
            [
                {
                    "page_num": 1,
                    "text": "\n".join(
                        [
                            "Pasal 8",
                            "(1) PJP wajib memenuhi seluruh kewajiban berikut:",
                            *items,
                        ]
                    ),
                }
            ],
            document_id="oversized-enumeration-fixture",
        )

        self.assertEqual(len([unit for unit in units if unit["unit_type"] == "huruf"]), 13)
        self.assertFalse(any(unit.get("legal_unit_role") == "enumeration_aggregate" for unit in units))

    def test_damaged_numberless_pasal_heading_does_not_contaminate_prior_leaf(self) -> None:
        units = parse_legal_units(
            [{"page_num": 2, "text": "Pasal 1\n(1) Bank wajib melapor.\nPasal"}],
            document_id="bare-pasal-fixture",
        )

        ayat = unit_by_path(units, pasal="Pasal 1", ayat="(1)")

        self.assertEqual(ayat["display_text"], "(1) Bank wajib melapor.")

    def test_displaced_wrapped_ayat_marker_does_not_create_fabricated_huruf(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 91,
                    "text": "\n".join(
                        [
                            "Pasal 25B",
                            "(1) Target waktu ditetapkan untuk:",
                            "c. pelampauan sebagaimana dimaksud dalam Pasal 25A ayat",
                            "huruf e ditetapkan paling lambat 18(1)",
                            "(delapan belas) bulan.",
                        ]
                    ),
                }
            ],
            document_id="wrapped-reading-order-fixture",
        )

        huruf_c = unit_by_path(units, pasal="Pasal 25B", ayat="(1)", huruf="huruf c")

        self.assertIn("Pasal 25A ayat (1) huruf e", huruf_c["display_text"])
        self.assertFalse(any(unit.get("legal_path", {}).get("huruf") == "huruf e" for unit in units))

    def test_split_pasal_number_is_reconstructed_as_reference_or_heading(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 8,
                    "text": "\n".join(
                        [
                            "Pasal 10",
                            "(1) Kewajiban sebagaimana dimaksud dalam",
                            "Pasal",
                            "9",
                            "tetap berlaku.",
                            "Pasal",
                            "11",
                            "Peraturan ini mulai berlaku.",
                        ]
                    ),
                }
            ],
            document_id="split-pasal-number-fixture",
        )

        ayat = unit_by_path(units, pasal="Pasal 10", ayat="(1)")
        next_pasal = unit_by_path(units, pasal="Pasal 11")

        self.assertIn("dimaksud dalam Pasal 9 tetap berlaku", ayat["display_text"])
        self.assertEqual(next_pasal["display_text"], "Pasal 11 Peraturan ini mulai berlaku.")

    def test_attachment_boundary_resets_promulgation_without_losing_annex_units(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 4,
                    "text": "Pasal 2\nPeraturan ini berlaku.\nDitetapkan di Jakarta",
                },
                {
                    "page_num": 5,
                    "text": "LAMPIRAN II\nPasal 1\n(1) Formulir wajib diisi.",
                },
            ],
            document_id="attachment-boundary-fixture",
        )

        annex = next(unit for unit in units if unit.get("legal_path", {}).get("ayat") == "(1)")

        self.assertEqual(annex["document_part"], "attachment")
        self.assertEqual(annex["legal_unit"]["document_part"], "attachment")

    def test_line_wrapped_promulgation_formula_does_not_contaminate_terminal_pasal(self) -> None:
        units = parse_legal_units(
            [
                {
                    "page_num": 5,
                    "text": "\n".join(
                        [
                            "Pasal 2",
                            "Peraturan ini mulai berlaku pada tanggal diundangkan.",
                            "Agar",
                            "setiap orang mengetahuinya, memerintahkan pengundangan.",
                        ]
                    ),
                }
            ],
            document_id="wrapped-promulgation-fixture",
        )

        pasal = unit_by_path(units, pasal="Pasal 2")
        promulgation = [unit for unit in units if unit["document_part"] == "promulgation"]

        self.assertNotIn("Agar setiap", pasal["display_text"])
        self.assertTrue(promulgation)

    def test_full_legal_hierarchy_has_parent_links_and_deterministic_ids(self) -> None:
        pages = [
            {
                "page_num": 1,
                "text": "\n".join(
                    [
                        "BAB I KETENTUAN UMUM",
                        "Bagian Kesatu",
                        "Paragraf 1",
                        "Pasal 1",
                        "(1) Ketentuan terdiri atas:",
                        "a. kewajiban:",
                        "1. menyampaikan laporan;",
                    ]
                ),
            }
        ]
        first = parse_legal_units(pages, document_id="hierarchy-fixture")
        second = parse_legal_units(pages, document_id="hierarchy-fixture")
        by_type = {unit["unit_type"]: unit for unit in first}

        self.assertEqual(
            set(by_type),
            {"bab", "bagian", "paragraf", "pasal", "ayat", "huruf", "angka"},
        )
        self.assertEqual(by_type["angka"]["parent_id"], by_type["huruf"]["node_id"])
        self.assertEqual(by_type["huruf"]["parent_id"], by_type["ayat"]["node_id"])
        self.assertEqual(
            [unit["node_id"] for unit in first],
            [unit["node_id"] for unit in second],
        )


if __name__ == "__main__":
    unittest.main()
