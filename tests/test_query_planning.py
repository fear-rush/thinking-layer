from __future__ import annotations

import unittest

from thinking_layer.retrieval.planning import build_query_plan


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


if __name__ == "__main__":
    unittest.main()
