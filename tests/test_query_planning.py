from __future__ import annotations

import unittest

from thinking_layer.retrieval.planning import build_query_plan
from thinking_layer.retrieval.search import direct_enumeration_aggregate_multiplier, planned_result_score


class QueryPlanningTests(unittest.TestCase):
    def test_compound_permission_question_gets_bounded_predicate_variant(self) -> None:
        plan = build_query_plan(
            "Di mana bank wajib menempatkan pusat data dan kapan boleh di luar Indonesia?",
            max_searches=8,
        )

        predicate_searches = [
            search for search in plan["searches"] if search["reason"] == "predicate:boleh:dapat"
        ]
        self.assertEqual(len(predicate_searches), 1)
        self.assertIn("kapan dapat di luar Indonesia", predicate_searches[0]["query"])

    def test_bank_slik_query_expands_to_ojk_reporting_plan(self) -> None:
        plan = build_query_plan("apa kewajiban bank terkait pelaporan SLIK?", max_searches=4)

        self.assertIn("OJK", plan["issuers"])
        self.assertIn("bank", plan["entities"])
        self.assertIn("reporting", plan["topics"])
        self.assertIn("slik", plan["topics"])
        self.assertEqual(plan["searches"][0]["reason"], "raw_user_query")
        self.assertTrue(any(search["reason"] == "topic:slik" for search in plan["searches"]))

    def test_cross_regulator_payment_query_keeps_both_issuers(self) -> None:
        plan = build_query_plan("komparasi peraturan OJK dan BI terkait penyedia jasa pembayaran", max_searches=8)

        self.assertIn("OJK", plan["issuers"])
        self.assertIn("BI", plan["issuers"])
        self.assertIn("pjp", plan["entities"])
        self.assertTrue(any(search.get("issuer") == "BI" for search in plan["searches"]))

    def test_ambiguous_institution_data_query_searches_both_regulators_with_legal_aliases(self) -> None:
        plan = build_query_plan(
            "Bolehkah lembaga keuangan membagikan data pelanggan ke perusahaan lain?",
            max_searches=8,
        )

        self.assertEqual(plan["ambiguity"], "institution_type")
        self.assertEqual(plan["issuers"], ["BI", "OJK"])
        predicate_searches = [search for search in plan["searches"] if search["reason"].startswith("predicate:")]
        self.assertEqual({search["issuer"] for search in predicate_searches}, {"BI", "OJK"})
        self.assertTrue(all("memberikan data konsumen" in search["query"].casefold() for search in predicate_searches))
        self.assertTrue(all("pihak lain" in search["query"].casefold() for search in predicate_searches))

    def test_explicit_unsupported_bappebti_scope_has_no_ojk_fallback_search(self) -> None:
        plan = build_query_plan("Menurut Bappebti, bukan OJK, berapa modal minimum pedagang aset kripto?")

        self.assertEqual(plan["unsupported_source"], "BAPPEBTI")
        self.assertEqual(plan["issuers"], [])
        self.assertEqual(plan["searches"], [])

    def test_named_regulated_subject_beats_late_cross_reference(self) -> None:
        search = {"reason": "raw_user_query", "query": "modal pedagang aset digital"}
        direct = planned_result_score(
            "Berapa modal minimum Pedagang Aset Keuangan Digital?",
            search,
            1,
            4,
            {
                "file_role": "primary_regulation",
                "document_title": "Perdagangan Aset Keuangan Digital",
                "assembled_text": "Pedagang wajib memiliki modal disetor paling sedikit Rp100.000.000.000,00.",
            },
        )
        cross_reference = planned_result_score(
            "Berapa modal minimum Pedagang Aset Keuangan Digital?",
            search,
            1,
            1,
            {
                "file_role": "primary_regulation",
                "document_title": "Perdagangan Aset Keuangan Digital",
                "assembled_text": (
                    "Bursa wajib mempertahankan ekuitas dari modal disetor dan memastikan kegiatan perdagangan "
                    "berjalan teratur, wajar, transparan, efektif, efisien, serta terlindungi dari gangguan; "
                    "ketentuan tersebut juga menjadi acuan bagi Pedagang."
                ),
            },
        )

        self.assertGreater(direct, cross_reference)

    def test_planned_results_prioritize_primary_regulations_over_guidance(self) -> None:
        search = {"reason": "raw_user_query", "query": "qris"}
        primary = planned_result_score(
            "qris",
            search,
            search_rank=1,
            result_rank=3,
            row={"file_role": "primary_regulation", "document_title": "QRIS"},
        )
        operational = planned_result_score(
            "qris",
            search,
            search_rank=1,
            result_rank=1,
            row={"file_role": "operational_requirement", "document_title": "QRIS matrix"},
        )
        faq = planned_result_score(
            "qris",
            search,
            search_rank=1,
            result_rank=1,
            row={"file_role": "secondary_faq", "document_title": "QRIS FAQ"},
        )

        self.assertGreater(primary, operational)
        self.assertGreater(operational, faq)

    def test_uniform_context_does_not_expand_marketing_topic(self) -> None:
        plan = build_query_plan(
            "apa ketentuan BI mengenai warna seragam petugas pemasaran bank?",
            max_searches=6,
        )

        self.assertNotIn("advertising_marketing", plan["topics"])
        self.assertEqual(len(plan["searches"]), 1)

    def test_explicit_enumeration_question_binds_subject_noun_and_marker(self) -> None:
        plan = build_query_plan("Apa aktivitas Penyedia Jasa Pembayaran?", max_searches=8)

        enumeration_searches = [search for search in plan["searches"] if search["reason"].startswith("direct_enumeration:")]
        self.assertEqual(
            [search["query"] for search in enumeration_searches],
            ["penyedia jasa pembayaran aktivitas meliputi", "pjp aktivitas meliputi"],
        )
        self.assertTrue(all(search["issuer"] == "BI" for search in enumeration_searches))
        self.assertTrue(all(search["role"] == "primary_regulation" for search in enumeration_searches))

    def test_non_enumeration_question_does_not_add_marker_search(self) -> None:
        plan = build_query_plan("Bagaimana perizinan Penyedia Jasa Pembayaran?", max_searches=8)

        self.assertFalse(any(search["reason"].startswith("direct_enumeration:") for search in plan["searches"]))

    def test_direct_enumeration_prefers_a_governing_ayat_aggregate_not_a_nested_list(self) -> None:
        search = {"reason": "direct_enumeration:aktivitas:meliputi", "query": "penyedia aktivitas meliputi"}
        governing_aggregate = planned_result_score(
            "apa aktivitas penyedia",
            search,
            search_rank=2,
            result_rank=5,
            row={
                "file_role": "primary_regulation",
                "document_title": "PBI Penyedia",
                "citation_admission": "enumeration_aggregate",
                "legal_path": {"pasal": "Pasal 2", "ayat": "(1)"},
            },
        )
        nested_aggregate = planned_result_score(
            "apa aktivitas penyedia",
            search,
            search_rank=2,
            result_rank=1,
            row={
                "file_role": "primary_regulation",
                "document_title": "PBI Penyedia",
                "citation_admission": "enumeration_aggregate",
                "legal_path": {"pasal": "Pasal 12", "ayat": "(1)", "huruf": "huruf b"},
            },
        )

        self.assertGreater(governing_aggregate, nested_aggregate)

    def test_direct_enumeration_multiplier_does_not_leak_to_title_or_entity_searches(self) -> None:
        governing_aggregate = {
            "citation_admission": "enumeration_aggregate",
            "legal_path": {"pasal": "Pasal 2", "ayat": "(1)"},
        }
        config = {"direct_enumeration_governing_ayat_multiplier": 5.0}

        self.assertEqual(
            direct_enumeration_aggregate_multiplier(
                {"reason": "title:direct_enumeration:aktivitas:meliputi"}, governing_aggregate, config
            ),
            1.0,
        )
        self.assertEqual(
            direct_enumeration_aggregate_multiplier(
                {"reason": "entity:pjp"}, governing_aggregate, config
            ),
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
