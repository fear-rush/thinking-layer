from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import thinking_layer.indexing.sqlite as sqlite_index
import thinking_layer.retrieval.search as retrieval_search
from thinking_layer.indexing.lexical import build_search_index
from thinking_layer.retrieval.planning import build_query_plan, parse_legal_query_constraints
from thinking_layer.retrieval.search import execute_query_plan


def legal_block(
    *,
    file_id: str,
    block_id: str,
    title: str,
    text: str,
    page: int,
    pasal: str,
    ayat: str | None = None,
    regulation_type: str,
    number: str,
    year: str,
    admission: str = "atomic_leaf",
) -> dict[str, object]:
    legal_path = {"pasal": pasal}
    unit_path = [pasal]
    if ayat:
        legal_path["ayat"] = ayat
        unit_path.append(ayat)
    source_ids = [block_id]
    return {
        "file_id": file_id,
        "block_id": block_id,
        "node_id": block_id,
        "canonical_id": f"{regulation_type}-{number}-{year}",
        "issuer": "BI" if regulation_type == "PBI" else "OJK",
        "source": "fixture",
        "source_priority": "primary",
        "file_role": "primary_regulation",
        "document_title": title,
        "regulation_type": regulation_type,
        "number": number,
        "year": year,
        "page_start": page,
        "page_end": page,
        "pasal": pasal,
        "ayat": ayat,
        "huruf": None,
        "legal_path": legal_path,
        "unit_path": unit_path,
        "retrieval_text": f"{' '.join(unit_path)}. {text}",
        "display_text": text,
        "assembled_text": text,
        "text": text,
        "source_block_ids": source_ids,
        "anchors": [{"page_start": page, "line_start": 1, "page_end": page, "line_end": 1}],
        "source_spans": [],
        "legal_unit": {"type": "ayat" if ayat else "pasal", "legal_path": legal_path, "source_block_ids": source_ids},
        "citation_admission": admission,
        "citation_quality": "document_page_pasal_ayat" if ayat else "document_page_pasal",
        "section_type": "enumeration_aggregate" if admission == "enumeration_aggregate" else ("ayat" if ayat else "pasal"),
        "block_type": "paragraph",
    }


class RetrievalLegalConstraintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        search_dir = Path(self.temp_dir.name) / "search_index"
        search_db = search_dir / "search.sqlite"
        self.patchers = [
            patch.object(sqlite_index, "SEARCH_INDEX_DIR", search_dir),
            patch.object(sqlite_index, "SEARCH_INDEX_DB", search_db),
            patch.object(retrieval_search, "SEARCH_INDEX_DB", search_db),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self) -> None:
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.temp_dir.cleanup()

    def write_index(self, blocks: list[dict[str, object]]) -> None:
        sqlite_index.write_sqlite_search_index(
            build_search_index(blocks),
            {"issuer": None, "role": None, "source": None, "include_secondary": True},
        )

    def assert_top_block(self, query: str, expected_block_id: str) -> None:
        plan = build_query_plan(query, max_searches=8)
        results = execute_query_plan(plan, limit=12)
        self.assertTrue(results, query)
        self.assertEqual(results[0]["block_id"], expected_block_id)
        self.assertTrue(all(retrieval_search.row_matches_legal_constraints(row, plan["legal_constraints"]) for row in results))

    def test_explicit_uka_pasal_two_ayat_one_beats_title_representative(self) -> None:
        title = "PBI No.19/7/PBI/2017 Pembawaan Uang Kertas Asing"
        self.write_index(
            [
                legal_block(
                    file_id="uka",
                    block_id="uka-wrong-representative",
                    title=title,
                    text="Pihak yang dapat menjadi Badan Berizin terdiri atas Bank dan KUPVA Bukan Bank.",
                    page=2,
                    pasal="Pasal 2",
                    ayat="(3)",
                    regulation_type="PBI",
                    number="19/7/PBI/2017",
                    year="2017",
                    admission="enumeration_aggregate",
                ),
                legal_block(
                    file_id="uka",
                    block_id="uka-threshold",
                    title=title,
                    text="Setiap pihak yang membawa UKA paling sedikit setara Rp1.000.000.000 wajib memperoleh izin Bank Indonesia.",
                    page=4,
                    pasal="Pasal 2",
                    ayat="(1)",
                    regulation_type="PBI",
                    number="19/7/PBI/2017",
                    year="2017",
                ),
            ]
        )

        self.assert_top_block(
            "Berapa batas pembawaan UKA berdasarkan Pasal 2 ayat (1) PBI 19/7/2017?",
            "uka-threshold",
        )

    def test_explicit_pojk_35_pasal_five_finds_secretary_duties(self) -> None:
        title = "Sekretaris Perusahaan Emiten atau Perusahaan Publik"
        self.write_index(
            [
                legal_block(
                    file_id="secretary",
                    block_id="secretary-wrong-representative",
                    title=title,
                    text="Kekosongan Sekretaris Perusahaan wajib diisi dalam jangka waktu tertentu.",
                    page=2,
                    pasal="Pasal 4",
                    regulation_type="Peraturan OJK",
                    number="35/POJK.04/2014",
                    year="2014",
                    admission="enumeration_aggregate",
                ),
                legal_block(
                    file_id="secretary",
                    block_id="secretary-duties",
                    title=title,
                    text="Fungsi sekretaris perusahaan melaksanakan tugas paling kurang mengikuti perkembangan Pasar Modal dan membantu tata kelola perusahaan.",
                    page=3,
                    pasal="Pasal 5",
                    regulation_type="Peraturan OJK",
                    number="35/POJK.04/2014",
                    year="2014",
                    admission="enumeration_aggregate",
                ),
            ]
        )

        self.assert_top_block(
            "Apa tugas Sekretaris Perusahaan berdasarkan Pasal 5 POJK Nomor 35/POJK.04/2014?",
            "secretary-duties",
        )

    def test_explicit_pojk_26_pasal_three_finds_solvency_obligation(self) -> None:
        title = "Pengelolaan Aset dan Liabilitas Perusahaan Asuransi dan Perusahaan Reasuransi"
        self.write_index(
            [
                legal_block(
                    file_id="insurance",
                    block_id="insurance-wrong-representative",
                    title=title,
                    text="Investasi pada reksa dana penyertaan terbatas harus memiliki peringkat investment grade.",
                    page=8,
                    pasal="Pasal 5",
                    ayat="(5)",
                    regulation_type="Peraturan OJK",
                    number="26 Tahun 2025",
                    year="2025",
                    admission="enumeration_aggregate",
                ),
                legal_block(
                    file_id="insurance",
                    block_id="insurance-solvency",
                    title=title,
                    text="Perusahaan wajib memenuhi Tingkat Solvabilitas paling rendah 100% dari MMBR dan menetapkan target internal paling rendah 120%.",
                    page=5,
                    pasal="Pasal 3",
                    ayat="(1)",
                    regulation_type="Peraturan OJK",
                    number="26 Tahun 2025",
                    year="2025",
                    admission="enumeration_aggregate",
                ),
            ]
        )

        self.assert_top_block(
            "Apa kewajiban Perusahaan berdasarkan Pasal 3 ayat (1) POJK Nomor 26 Tahun 2025?",
            "insurance-solvency",
        )

    def test_unanchored_uka_question_discovers_title_then_threshold_clause(self) -> None:
        uka_title = "PBI No.19/7/PBI/2017 - Pembawaan Uang Kertas Asing Ke Dalam dan Ke Luar Daerah Pabean Indonesia"
        self.write_index(
            [
                legal_block(
                    file_id="uka",
                    block_id="uka-representative",
                    title=uka_title,
                    text="Badan Berizin terdiri atas Bank dan KUPVA Bukan Bank.",
                    page=2,
                    pasal="Pasal 1",
                    regulation_type="PBI",
                    number="19/7/PBI/2017",
                    year="2017",
                ),
                legal_block(
                    file_id="uka",
                    block_id="uka-unanchored-threshold",
                    title=uka_title,
                    text="Setiap pihak yang melakukan Pembawaan UKA paling sedikit setara Rp1.000.000.000 wajib memperoleh Izin Pembawaan UKA dari Bank Indonesia.",
                    page=4,
                    pasal="Pasal 2",
                    ayat="(1)",
                    regulation_type="PBI",
                    number="19/7/PBI/2017",
                    year="2017",
                ),
                legal_block(
                    file_id="uka-report",
                    block_id="uka-report-row",
                    title="Laporan Pembawaan Uang Kertas Asing",
                    text="Pelapor menyampaikan laporan Pembawaan UKA melalui surat elektronik.",
                    page=4,
                    pasal="Pasal 6",
                    regulation_type="PADG",
                    number="24/15/PADG/2022",
                    year="2022",
                ),
            ]
        )

        results = execute_query_plan(
            build_query_plan("Berapa batas nilai pembawaan uang kertas asing yang wajib memperoleh izin BI?", 8),
            limit=12,
        )

        self.assertTrue(results)
        self.assertEqual(results[0]["block_id"], "uka-unanchored-threshold")
        self.assertTrue(str(results[0]["_plan_reason"]).startswith("title_discovery:"))

    def test_unqualified_bank_it_query_excludes_bpr_near_match(self) -> None:
        bank_umum_title = "POJK 11 Tahun 2022 Penyelenggaraan Teknologi Informasi oleh Bank Umum"
        bpr_title = "POJK 34 Tahun 2025 Penyelenggaraan Teknologi Informasi oleh Bank Perekonomian Rakyat"
        self.write_index(
            [
                legal_block(
                    file_id="bank-umum",
                    block_id="bank-umum-data-center",
                    title=bank_umum_title,
                    text="Bank wajib menempatkan Pusat Data dan Pusat Pemulihan Bencana di wilayah Indonesia.",
                    page=22,
                    pasal="Pasal 35",
                    ayat="(1)",
                    regulation_type="Peraturan OJK",
                    number="11 Tahun 2022",
                    year="2022",
                ),
                legal_block(
                    file_id="bpr",
                    block_id="bpr-data-center",
                    title=bpr_title,
                    text="BPR wajib menempatkan Pusat Data dan Pusat Pemulihan Bencana di wilayah Indonesia.",
                    page=22,
                    pasal="Pasal 35",
                    ayat="(1)",
                    regulation_type="Peraturan OJK",
                    number="34 Tahun 2025",
                    year="2025",
                ),
            ]
        )

        results = execute_query_plan(
            build_query_plan(
                "Di mana bank wajib menempatkan pusat data dan pusat pemulihan bencana, dan kapan boleh di luar Indonesia?",
                8,
            ),
            limit=12,
        )

        self.assertTrue(results)
        self.assertEqual({row["file_id"] for row in results}, {"bank-umum"})

    def test_prohibition_predicate_search_selects_operational_clause(self) -> None:
        title = "POJK 6 Tahun 2022 Perlindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan"
        self.write_index(
            [
                legal_block(
                    file_id="consumer",
                    block_id="data-prohibition",
                    title=title,
                    text="PUJK dilarang memberikan data pribadi Konsumen kepada pihak lain sebagai syarat penggunaan layanan.",
                    page=8,
                    pasal="Pasal 11",
                    ayat="(1)",
                    regulation_type="Peraturan OJK",
                    number="6 Tahun 2022",
                    year="2022",
                    admission="enumeration_aggregate",
                ),
                legal_block(
                    file_id="consumer",
                    block_id="data-source-notice",
                    title=title,
                    text="PUJK wajib memberitahukan Konsumen mengenai sumber data pribadi yang diperoleh.",
                    page=8,
                    pasal="Pasal 11",
                    ayat="(6)",
                    regulation_type="Peraturan OJK",
                    number="6 Tahun 2022",
                    year="2022",
                ),
            ]
        )

        plan = build_query_plan("Apa larangan OJK bagi PUJK terkait data pribadi konsumen?", 8)
        results = execute_query_plan(plan, limit=12)

        self.assertTrue(results)
        self.assertEqual(results[0]["block_id"], "data-prohibition")
        self.assertTrue(any(str(search["reason"]).startswith("predicate:") for search in plan["searches"]))

    def test_primary_technology_topic_scope_beats_generic_reporting_title(self) -> None:
        incident = legal_block(
            file_id="bank-it",
            block_id="incident-deadlines",
            title="Penyelenggaraan Teknologi Informasi Oleh Bank Umum",
            text=(
                "Bank wajib menyampaikan notifikasi awal paling lama 24 jam dan laporan insiden TI "
                "paling lama 5 hari kerja setelah insiden diketahui."
            ),
            page=36,
            pasal="Pasal 60",
            ayat="(1)",
            regulation_type="Peraturan OJK",
            number="11 Tahun 2022",
            year="2022",
            admission="enumeration_aggregate",
        )
        reporting = legal_block(
            file_id="bank-reporting",
            block_id="generic-reporting",
            title="Transparansi dan Publikasi Laporan Bank",
            text="Bank wajib menyampaikan laporan publikasi keuangan tahunan kepada OJK.",
            page=6,
            pasal="Pasal 11",
            ayat="(1)",
            regulation_type="Peraturan OJK",
            number="37 Tahun 2019",
            year="2019",
            admission="enumeration_aggregate",
        )
        self.write_index([incident, reporting])

        results = execute_query_plan(
            build_query_plan(
                "Kapan bank harus mengirim notifikasi awal dan laporan insiden TI signifikan kepada OJK?",
                8,
            ),
            limit=12,
        )

        self.assertEqual(results[0]["block_id"], "incident-deadlines")

    def test_normal_query_still_uses_global_bm25_without_a_title_hit(self) -> None:
        self.write_index(
            [
                legal_block(
                    file_id="reporting",
                    block_id="late-report-sanction",
                    title="Ketentuan Operasional Bank",
                    text="Bank yang terlambat menyampaikan laporan dikenai sanksi administratif berupa teguran tertulis.",
                    page=9,
                    pasal="Pasal 12",
                    regulation_type="Peraturan OJK",
                    number="1 Tahun 2024",
                    year="2024",
                )
            ]
        )

        plan = build_query_plan("Apa sanksi jika bank terlambat menyampaikan laporan?", max_searches=1)
        results = execute_query_plan(plan, limit=5)

        self.assertEqual(results[0]["block_id"], "late-report-sanction")
        self.assertEqual(results[0]["_plan_reason"], "raw_user_query")

    def test_title_representative_is_not_emitted_when_passage_search_has_no_hit(self) -> None:
        representative = {
            "file_id": "document-1",
            "block_id": "arbitrary-title-representative",
            "document_title": "Relevant Document",
        }
        plan = {
            "raw_query": "relevant document predicate",
            "legal_constraints": {},
            "searches": [{"query": "relevant document predicate", "issuer": None, "role": None, "include_secondary": True, "reason": "raw_user_query"}],
        }
        with (
            patch.object(retrieval_search, "sqlite_index_is_current", return_value=True),
            patch.object(retrieval_search, "sqlite_metadata", return_value={}),
            patch.object(retrieval_search, "sqlite_title_search", return_value=[representative]),
            patch.object(retrieval_search, "sqlite_search", return_value=[]),
            patch.object(retrieval_search.sqlite3, "connect") as connect,
        ):
            connect.return_value.__enter__.return_value = connect.return_value
            results = execute_query_plan(plan, limit=5)

        self.assertEqual(results, [])

    def test_constraint_parser_normalizes_explicit_anchors(self) -> None:
        self.assertEqual(
            parse_legal_query_constraints("Pasal 5 ayat (2) huruf b POJK Nomor 35/POJK.04/2014"),
            {
                "pasal": "Pasal 5",
                "ayat": "(2)",
                "huruf": "huruf b",
                "regulation_type": "POJK",
                "regulation_number": "35",
                "year": "2014",
            },
        )

    def test_document_year_is_not_misparsed_as_a_regulation_number(self) -> None:
        self.assertEqual(
            parse_legal_query_constraints(
                "Berapa modal disetor minimum Pedagang Aset Keuangan Digital menurut perubahan POJK tahun 2025?"
            ),
            {"regulation_type": "POJK", "year": "2025"},
        )


if __name__ == "__main__":
    unittest.main()
