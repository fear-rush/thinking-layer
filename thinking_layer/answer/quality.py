from __future__ import annotations

import re
from typing import Any

from ..config.heuristics import heuristic_section
from .composer import claim_is_complete

def contains_all_terms(text: str, terms: list[str]) -> list[str]:
    lower = text.lower()
    return [term for term in terms if term.lower() in lower]

def source_lines_from_answer(answer_text: str) -> list[str]:
    return [line for line in answer_text.splitlines() if re.match(r"^\[\d+\]\s+", line.strip())]


def _source_block_ids(citation: dict[str, Any]) -> list[str]:
    source_block_ids = citation["source_block_ids"]
    return [str(block_id) for block_id in source_block_ids if block_id]


def _page_number(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _structured_contract_checks(
    findings: list[dict[str, Any]], citations: list[dict[str, Any]], status: str | None
) -> dict[str, bool]:
    """Validate claim-to-citation provenance without requiring an LLM judge."""

    citation_ids = [str(citation.get("id") or "") for citation in citations]
    known_citation_ids = set(citation_ids) - {""}
    referenced_citation_ids = {
        str(citation_id)
        for finding in findings
        for citation_id in (finding.get("citation_ids") or [])
        if citation_id
    }
    valid_targets = all(
        bool(citation.get("file_id"))
        and bool(_source_block_ids(citation))
        and _page_number(citation.get("page_start") or citation.get("page")) > 0
        and _page_number(citation.get("page_end") or citation.get("page_start") or citation.get("page"))
        >= _page_number(citation.get("page_start") or citation.get("page"))
        for citation in citations
    )
    valid_finding_content = all(
        bool(str(finding.get("text") or "").strip())
        and claim_is_complete(str(finding.get("text") or ""))
        and finding.get("status") == "supported"
        and bool(finding.get("citation_ids"))
        and {str(value) for value in finding.get("citation_ids") or []}.issubset(known_citation_ids)
        for finding in findings
    )
    valid_findings = valid_finding_content and (bool(findings) if status != "not_found" else not findings)
    return {
        "finding_limit_respected": len(findings) <= 3,
        "findings_are_complete_and_supported": valid_findings,
        "citation_ids_are_unique": len(citation_ids) == len(set(citation_ids)) and all(citation_ids),
        "citation_targets_are_valid": valid_targets,
        "no_orphan_citations": set(citation_ids) == referenced_citation_ids,
        "not_found_has_no_findings": status != "not_found" or not findings,
    }

def evaluate_answer_quality(spec: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    config = heuristic_section("evaluation_rubrics", "answer_quality")
    answer_text = answer.get("answer") or ""
    expected_behavior = spec.get("expected_behavior") or "answerable"
    status = answer.get("status")
    confidence = answer.get("confidence") or {}
    citation_count = int(answer.get("citation_count") or 0)
    documents_used = answer.get("documents_used") or []
    findings = list(answer.get("findings") or [])
    citations = list(answer.get("citations") or [])
    structured = "findings" in answer or any(citation.get("id") for citation in citations)
    source_lines = source_lines_from_answer(answer_text)

    required_terms = spec.get("required_terms") or []
    required_uncertainty_terms = spec.get("required_uncertainty_terms") or []
    required_citation_terms = spec.get("required_citation_terms") or []
    required_issuers = spec.get("required_issuers") or []
    min_citations = int(
        spec.get(
            "min_citations",
            int(config.get("default_min_citations", 1)) if expected_behavior != "not_found" else int(config.get("not_found_min_citations", 0)),
        )
    )
    max_answer_chars = int(spec.get("max_answer_chars", int(config.get("default_max_answer_chars", 5000))))

    display_text = "\n".join(
        [answer_text, str(answer.get("summary") or "")]
        + [str(finding.get("text") or "") for finding in findings]
    )
    citation_display_text = "\n".join(
        list(source_lines)
        + [str(citation.get("text") or "") for citation in citations]
    )
    term_hits = contains_all_terms(display_text, required_terms)
    uncertainty_hits = contains_all_terms(answer_text, required_uncertainty_terms)
    citation_term_hits = contains_all_terms(citation_display_text, required_citation_terms)
    issuer_hits = sorted(
        {
            value
            for value in [
                *(doc.get("issuer") for doc in documents_used),
                *(citation.get("issuer") for citation in citations),
            ]
            if value in required_issuers
        }
    )
    noisy_hits = [pattern for pattern in config.get("noisy_answer_patterns", []) if re.search(pattern, answer_text, flags=re.IGNORECASE)]
    truncated_bullets = [
        line.strip()
        for line in answer_text.splitlines()
        if line.strip().startswith("- ") and re.match(r"^-\s+[a-z]", line.strip())
    ]
    source_line_count = len(citations) if structured else len(source_lines)
    primary_source_count = sum(
        1
        for document in documents_used
        if document.get("source_priority") == "primary" or document.get("file_role") == "primary_regulation"
    )
    if not primary_source_count and not structured:
        primary_source_count = sum(1 for line in source_lines if "; primary;" in line)
    primary_rate = primary_source_count / max(1, source_line_count)

    checks: dict[str, bool] = {}
    checks["status_matches_expected"] = (
        status == "not_found" if expected_behavior == "not_found" else status in {"answerable", "partial"}
    )
    checks["not_found_has_no_citations"] = not (expected_behavior == "not_found" and citation_count > 0)
    checks["has_required_terms"] = len(term_hits) == len(required_terms)
    checks["has_uncertainty_terms"] = len(uncertainty_hits) == len(required_uncertainty_terms)
    checks["has_required_citation_terms"] = len(citation_term_hits) == len(required_citation_terms)
    checks["has_min_citations"] = citation_count >= min_citations
    checks["source_lines_match_citation_count"] = source_line_count == citation_count
    checks["has_required_issuers"] = len(issuer_hits) == len(required_issuers)
    checks["primary_sources_first_enough"] = expected_behavior == "not_found" or primary_rate >= float(config.get("primary_sources_first_threshold", 0.75))
    checks["not_too_long"] = len(answer_text) <= max_answer_chars
    checks["no_noisy_fragments"] = not noisy_hits
    checks["no_truncated_bullets"] = not truncated_bullets
    checks["partial_has_uncertainty"] = expected_behavior != "partial" or "parsial" in answer_text.lower()
    if structured:
        checks.update(_structured_contract_checks(findings, citations, status))
    else:
        # Reports created before the structured response contract remain valid.
        checks.update(
            {
                "finding_limit_respected": True,
                "findings_are_complete_and_supported": True,
                "citation_ids_are_unique": True,
                "citation_targets_are_valid": True,
                "no_orphan_citations": True,
                "not_found_has_no_findings": True,
            }
        )

    weights = config.get("weights") or {}
    score = min(1.0, sum(weight for key, weight in weights.items() if checks[key]))
    hard_checks = config.get("hard_checks") or []
    failure_reasons = [key for key in hard_checks if not checks[key]]
    warnings = [key for key, value in checks.items() if not value and key not in hard_checks]
    accepted = score >= float(config.get("accepted_threshold", 0.86)) and not failure_reasons

    return {
        "id": spec.get("id"),
        "query": spec.get("query"),
        "expected_behavior": expected_behavior,
        "score": round(score, 3),
        "accepted": accepted,
        "status": status,
        "confidence": confidence,
        "citation_count": citation_count,
        "finding_count": len(findings),
        "structured": structured,
        "source_line_count": source_line_count,
        "answer_chars": len(answer_text),
        "required_terms": required_terms,
        "term_hits": term_hits,
        "required_uncertainty_terms": required_uncertainty_terms,
        "uncertainty_hits": uncertainty_hits,
        "required_citation_terms": required_citation_terms,
        "citation_term_hits": citation_term_hits,
        "required_issuers": required_issuers,
        "issuer_hits": issuer_hits,
        "primary_rate": round(primary_rate, 3),
        "noisy_hits": noisy_hits,
        "truncated_bullets": truncated_bullets,
        "checks": checks,
        "failure_reasons": failure_reasons,
        "warnings": warnings,
    }
