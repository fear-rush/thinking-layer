from __future__ import annotations

import copy
import json
import sqlite3
import tempfile
import unittest
import zlib
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from thinking_layer.evaluation.golden import (
    acceptance_gate_passed,
    citation_matches_variant,
    compare_summaries,
    evaluate_golden_answer,
    load_golden_suite,
    preflight_exact_targets,
    run_suite,
    select_cases,
    summarize,
    validate_golden_suite,
)


class GoldenEvaluationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_golden_suite()
        cls.gates = cls.suite["metadata"]["gates"]

    def test_suite_is_valid_and_covers_multiple_documents_and_behaviors(self) -> None:
        self.assertEqual(validate_golden_suite(self.suite), [])
        self.assertGreaterEqual(len(self.suite["cases"]), 40)
        categories = Counter(case["category"] for case in self.suite["cases"])
        self.assertGreaterEqual(categories["direct_exact"], 8)
        self.assertGreaterEqual(categories["enumeration_exact"], 2)
        self.assertGreaterEqual(categories["amendment_exact"], 2)
        self.assertGreaterEqual(categories["ambiguity"], 2)
        self.assertGreaterEqual(categories["no_answer"], 2)
        self.assertGreaterEqual(categories["parser_boundary"], 4)
        self.assertGreaterEqual(categories["lifecycle_unknown"], 1)
        self.assertGreaterEqual(categories["table_refusal"], 1)
        self.assertGreaterEqual(categories["governance_exact"], 1)
        issuers = {
            variant["issuer"]
            for case in self.suite["cases"]
            for target in case["expected"]["citations"]["targets"]
            for variant in target["variants"]
        }
        self.assertEqual(issuers, {"BI", "OJK"})

    def test_every_answerable_target_pins_file_page_legal_path_and_text(self) -> None:
        for case in self.suite["cases"]:
            if case["expected"]["statuses"] == ["not_found"]:
                continue
            citations_spec = case["expected"]["citations"]
            for target in [
                *(citations_spec.get("targets") or []),
                *(citations_spec.get("allowed_targets") or []),
            ]:
                for variant in target["variants"]:
                    with self.subTest(case=case["id"], target=target["name"]):
                        self.assertTrue(variant["issuer"])
                        self.assertTrue(variant["file_id"])
                        self.assertGreater(variant["page_start"], 0)
                        self.assertGreaterEqual(variant["page_end"], variant["page_start"])
                        self.assertTrue(variant["legal_path"])
                        self.assertTrue(variant["text_terms"])

    def test_exact_match_rejects_right_document_with_wrong_article_or_page(self) -> None:
        case = next(case for case in self.suite["cases"] if case["id"] == "bi_qris_mandatory")
        variant = case["expected"]["citations"]["targets"][0]["variants"][0]
        citation = {
            "issuer": "BI",
            "file_id": variant["file_id"],
            "page_start": 6,
            "page_end": 6,
            "legal_path": {"pasal": "Pasal 6", "ayat": "(1)"},
            "excerpt": "QRIS wajib digunakan untuk pembayaran dengan QR Code Pembayaran.",
        }
        self.assertTrue(citation_matches_variant(citation, variant))
        wrong_article = {**citation, "legal_path": {"pasal": "Pasal 8", "ayat": "(1)"}}
        wrong_page = {**citation, "page_start": 8, "page_end": 8}
        self.assertFalse(citation_matches_variant(wrong_article, variant))
        self.assertFalse(citation_matches_variant(wrong_page, variant))

    def test_answer_fails_when_only_off_target_citations_are_present(self) -> None:
        case = next(case for case in self.suite["cases"] if case["id"] == "bi_qris_mandatory")
        answer = self._supported_answer(case)
        answer["citations"][0]["legal_path"] = {"pasal": "Pasal 8", "ayat": "(2)"}
        result = evaluate_golden_answer(case, answer, self.gates)
        self.assertFalse(result["accepted"])
        self.assertIn("exact_targets", result["failure_reasons"])

    def test_genuinely_relevant_allowed_target_counts_for_precision_only(self) -> None:
        case = next(case for case in self.suite["cases"] if case["id"] == "bi_qris_mandatory")
        answer = self._supported_answer(case)
        allowed = copy.deepcopy(case["expected"]["citations"]["allowed_targets"][0]["variants"][0])
        answer["citations"].append(
            {
                "id": "c2",
                "issuer": allowed["issuer"],
                "file_id": allowed["file_id"],
                "block_id": "allowed-block",
                "source_block_ids": ["allowed-block"],
                "page_start": allowed["page_start"],
                "page_end": allowed["page_end"],
                "legal_path": allowed["legal_path"],
                "anchors": [{"page_start": allowed["page_start"], "page_end": allowed["page_end"]}],
                "excerpt": " ".join(allowed["text_terms"]),
            }
        )
        result = evaluate_golden_answer(case, answer, self.gates)
        self.assertTrue(result["accepted"], result)
        self.assertEqual(result["citation_precision"], 1.0)
        self.assertEqual(result["allowed_target_hits"], ["qris-application-qualifier"])

    def test_not_found_is_strictly_citation_and_finding_free(self) -> None:
        case = next(case for case in self.suite["cases"] if case["id"] == "not_found_medical_advice")
        answer = {
            "status": "not_found",
            "answer": "Tidak ditemukan dukungan dokumen yang tersedia.",
            "summary": "",
            "findings": [],
            "citations": [],
            "limitations": [],
        }
        self.assertTrue(evaluate_golden_answer(case, answer, self.gates)["accepted"])
        answer["citations"] = [{"issuer": "OJK"}]
        result = evaluate_golden_answer(case, answer, self.gates)
        self.assertFalse(result["accepted"])
        self.assertFalse(result["checks"]["exact_targets"])

    def test_lifecycle_and_table_boundaries_require_empty_evidence(self) -> None:
        for case_id in ("lifecycle_unknown_pawnshop_regulation", "seojk_table_computation_refusal"):
            case = next(case for case in self.suite["cases"] if case["id"] == case_id)
            self.assertTrue(case["expected"]["citations"]["must_be_empty"])
            self.assertEqual(case["expected"]["citations"]["targets"], [])
            required = case["expected"]["answer"]["required_term_groups"][0][0]
            uncertainty = case["expected"]["answer"]["uncertainty_terms"][0]
            answer = {
                "status": "partial",
                "answer": f"{required}; {uncertainty}.",
                "summary": "",
                "findings": [],
                "citations": [],
                "limitations": [],
            }
            result = evaluate_golden_answer(case, answer, self.gates)
            self.assertTrue(result["accepted"], result)

    def test_table_refusal_accepts_consistent_not_found_phrase(self) -> None:
        case = next(
            case for case in self.suite["cases"] if case["id"] == "seojk_table_computation_refusal"
        )
        answer = {
            "status": "not_found",
            "answer": "Tidak ditemukan dalam dokumen yang tersedia.",
            "summary": "Tidak ditemukan dalam dokumen yang tersedia.",
            "findings": [],
            "citations": [],
            "limitations": ["Sistem tidak akan menyimpulkan tanpa dukungan dokumen."],
        }
        result = evaluate_golden_answer(case, answer, self.gates)
        self.assertTrue(result["accepted"], result)

    def test_requested_regulatory_matrix_is_present(self) -> None:
        ids = {case["id"] for case in self.suite["cases"]}
        required_ids = {
            "bi_consumer_data_confidentiality",
            "bi_prohibited_standard_clauses",
            "bi_complaint_fee_prohibited",
            "bi_oral_complaint_five_days",
            "bi_written_complaint_twenty_days",
            "bi_written_complaint_required_information",
            "bi_apu_beneficial_owner_verification",
            "bi_apu_edd_high_risk",
            "ojk_exoneration_clauses_prohibited",
            "ojk_complaint_fee_prohibited",
            "ojk_bank_it_data_center_location",
            "ojk_bank_it_incident_deadlines",
            "bi_pip_ongoing_capital_tiers",
            "ojk_bmpk_liquidity_placement_limit",
            "ojk_bpr_governance_conflict_disclosure",
        }
        self.assertTrue(required_ids.issubset(ids), required_ids - ids)

    def test_synthetic_exact_answer_passes_all_hard_gates(self) -> None:
        case = next(case for case in self.suite["cases"] if case["id"] == "ojk_insurance_marketing_information")
        result = evaluate_golden_answer(case, self._supported_answer(case), self.gates)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["failure_reasons"], [])

    def test_smoke_tier_is_a_balanced_deterministic_subset(self) -> None:
        smoke = select_cases(self.suite, tier="smoke")
        smoke_ids = set(self.suite["metadata"]["tiers"]["smoke"])
        expected_ids = [case["id"] for case in self.suite["cases"] if case["id"] in smoke_ids]
        self.assertEqual([case["id"] for case in smoke], expected_ids)
        self.assertEqual(len(smoke), 13)
        self.assertEqual(len(select_cases(self.suite, tier="full")), 45)
        categories = {case["category"] for case in smoke}
        self.assertTrue({"direct_exact", "enumeration_exact", "cross_document", "table_refusal", "no_answer"}.issubset(categories))
        issuers = {
            variant["issuer"]
            for case in smoke
            for target in case["expected"]["citations"]["targets"]
            for variant in target["variants"]
        }
        self.assertEqual(issuers, {"BI", "OJK"})

    def test_case_and_category_filters_intersect_and_preserve_fixture_order(self) -> None:
        selected = select_cases(
            self.suite,
            tier="full",
            case_ids=["ojk_personal_data_prohibition,bi_qris_mandatory", "bi_pip_core_activities"],
            categories=["direct_exact"],
        )
        expected = [
            case["id"]
            for case in self.suite["cases"]
            if case["id"] in {"ojk_personal_data_prohibition", "bi_qris_mandatory", "bi_pip_core_activities"}
            and case["category"] == "direct_exact"
        ]
        self.assertEqual([case["id"] for case in selected], expected)
        with self.assertRaisesRegex(ValueError, "unknown case ids"):
            select_cases(self.suite, case_ids=["missing_case"])
        with self.assertRaisesRegex(ValueError, "unknown categories"):
            select_cases(self.suite, categories=["missing_category"])
        with self.assertRaisesRegex(ValueError, "selected no golden cases"):
            select_cases(
                self.suite,
                tier="smoke",
                case_ids=["bi_qris_mandatory"],
                categories=["no_answer"],
            )

    def test_exact_target_preflight_reports_present_and_missing_units(self) -> None:
        case = copy.deepcopy(
            next(case for case in self.suite["cases"] if case["id"] == "bi_qris_mandatory")
        )
        case["expected"]["citations"].pop("allowed_targets", None)
        variant = case["expected"]["citations"]["targets"][0]["variants"][0]
        block = {
            "issuer": variant["issuer"],
            "file_id": variant["file_id"],
            "page_start": variant["page_start"],
            "page_end": variant["page_end"],
            "legal_path": variant["legal_path"],
            "display_text": " ".join(variant["text_terms"]),
        }
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "search.sqlite3"
            connection = sqlite3.connect(database)
            try:
                connection.execute("CREATE TABLE docs (file_id TEXT, block_json BLOB)")
                connection.execute(
                    "INSERT INTO docs (file_id, block_json) VALUES (?, ?)",
                    (variant["file_id"], zlib.compress(json.dumps(block).encode("utf-8"))),
                )
                connection.commit()
            finally:
                connection.close()

            present = preflight_exact_targets([case], database)
            self.assertTrue(present["passed"], present)
            self.assertEqual(present["checked_variants"], present["matched_variants"])

            missing_case = copy.deepcopy(case)
            missing_case["expected"]["citations"]["targets"][0]["variants"][0]["legal_path"] = {
                "pasal": "Pasal 999"
            }
            missing = preflight_exact_targets([missing_case], database)
            self.assertFalse(missing["passed"])
            self.assertEqual(missing["matched_variants"], len(missing_case["expected"]["citations"]["targets"][0]["variants"]) - 1)
            self.assertEqual(missing["failures"][0]["case_id"], case["id"])

    def test_run_suite_records_latency_without_changing_evaluation_contract(self) -> None:
        case = next(case for case in self.suite["cases"] if case["id"] == "bi_qris_mandatory")
        payload = copy.deepcopy(self.suite)
        payload["cases"] = [copy.deepcopy(case)]
        payload["metadata"]["tiers"] = {"full": "all", "smoke": [case["id"]]}
        with patch(
            "thinking_layer.evaluation.golden.build_answer",
            return_value=self._supported_answer(case),
        ):
            rows = run_suite(payload, tier="smoke")
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["evaluation"]["accepted"])
        self.assertGreaterEqual(rows[0]["evaluation"]["latency_ms"], 0.0)

    def test_summary_and_prior_report_comparison_include_failures_and_latency(self) -> None:
        rows = [
            {
                "evaluation": {
                    "accepted": True,
                    "score": 1.0,
                    "category": "direct_exact",
                    "failure_reasons": [],
                    "latency_ms": 100.0,
                }
            },
            {
                "evaluation": {
                    "accepted": False,
                    "score": 0.6,
                    "category": "direct_exact",
                    "failure_reasons": ["exact_targets", "citation_precision"],
                    "latency_ms": 200.0,
                }
            },
        ]
        current = summarize(rows)
        self.assertEqual(current["accepted"], 1)
        self.assertEqual(current["hard_failure_counts"], {"citation_precision": 1, "exact_targets": 1})
        self.assertEqual(
            current["latency_ms"],
            {"p50": 150.0, "p95": 195.0, "max": 200.0, "total": 300.0},
        )
        prior = {
            **current,
            "accepted": 0,
            "acceptance_rate": 0.0,
            "average_score": 0.5,
            "hard_failure_counts": {"exact_targets": 2},
            "latency_ms": {"p50": 175.0, "p95": 250.0, "max": 225.0},
        }
        comparison = compare_summaries(current, prior)
        self.assertEqual(comparison["accepted_delta"], 1)
        self.assertEqual(comparison["acceptance_rate_delta"], 0.5)
        self.assertEqual(comparison["average_score_delta"], 0.3)
        self.assertEqual(
            comparison["latency_ms_delta"],
            {"p50": -25.0, "p95": -55.0, "max": -25.0},
        )
        self.assertEqual(
            comparison["hard_failure_count_delta"],
            {"citation_precision": 1, "exact_targets": -1},
        )

    def test_acceptance_gate_requires_every_selected_live_case(self) -> None:
        self.assertTrue(acceptance_gate_passed({"accepted": 3, "total": 3}))
        self.assertFalse(acceptance_gate_passed({"accepted": 2, "total": 3}))
        self.assertFalse(acceptance_gate_passed({"accepted": 0, "total": 0}))

    def test_validation_rejects_unknown_smoke_case(self) -> None:
        payload = copy.deepcopy(self.suite)
        payload["metadata"]["tiers"]["smoke"].append("missing_case")
        self.assertTrue(any("unknown ids" in error for error in validate_golden_suite(payload)))

    @staticmethod
    def _supported_answer(case: dict[str, object]) -> dict[str, object]:
        expected = case["expected"]  # type: ignore[index]
        target = expected["citations"]["targets"][0]  # type: ignore[index]
        variant = copy.deepcopy(target["variants"][0])
        required_groups = expected.get("answer", {}).get("required_term_groups", [])  # type: ignore[union-attr]
        answer_text = ". ".join(group[0] for group in required_groups)
        citation = {
            "id": "c1",
            "issuer": variant["issuer"],
            "file_id": variant["file_id"],
            "block_id": "gold-block",
            "source_block_ids": ["gold-block"],
            "page_start": variant["page_start"],
            "page_end": variant["page_end"],
            "legal_path": variant["legal_path"],
            "anchors": [{"page_start": variant["page_start"], "page_end": variant["page_end"]}],
            "excerpt": " ".join(variant["text_terms"]),
        }
        return {
            "status": expected["statuses"][0],  # type: ignore[index]
            "answer": answer_text,
            "summary": "",
            "findings": [{"id": "f1", "text": answer_text, "citation_ids": ["c1"]}],
            "citations": [citation],
            "limitations": [],
        }


if __name__ == "__main__":
    unittest.main()
