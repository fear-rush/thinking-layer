from __future__ import annotations

import unittest

from thinking_layer.retrieval.planning import build_query_plan
from thinking_layer.retrieval.search import planned_result_score


class QueryPlanningTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
