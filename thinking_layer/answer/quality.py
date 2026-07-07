from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from ..config.heuristics import heuristic_section
from ..config.paths import ANSWER_QUALITY_QUESTIONS_PATH, REPORTS_DIR, ROOT
from .composer import build_answer
from ..evaluation.evidence import load_gold_questions

def contains_all_terms(text: str, terms: list[str]) -> list[str]:
    lower = text.lower()
    return [term for term in terms if term.lower() in lower]

def source_lines_from_answer(answer_text: str) -> list[str]:
    return [line for line in answer_text.splitlines() if re.match(r"^\[\d+\]\s+", line.strip())]

def evaluate_answer_quality(spec: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    config = heuristic_section("evaluation_rubrics", "answer_quality")
    answer_text = answer.get("answer") or ""
    expected_behavior = spec.get("expected_behavior") or "answerable"
    status = answer.get("status")
    confidence = answer.get("confidence") or {}
    citation_count = int(answer.get("citation_count") or 0)
    documents_used = answer.get("documents_used") or []
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

    term_hits = contains_all_terms(answer_text, required_terms)
    uncertainty_hits = contains_all_terms(answer_text, required_uncertainty_terms)
    citation_term_hits = contains_all_terms("\n".join(source_lines), required_citation_terms)
    issuer_hits = sorted({doc.get("issuer") for doc in documents_used if doc.get("issuer") in required_issuers})
    noisy_hits = [pattern for pattern in config.get("noisy_answer_patterns", []) if re.search(pattern, answer_text, flags=re.IGNORECASE)]
    truncated_bullets = [
        line.strip()
        for line in answer_text.splitlines()
        if line.strip().startswith("- ") and re.match(r"^-\s+[a-z]", line.strip())
    ]
    source_line_count = len(source_lines)
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

def write_answer_quality_report(rows: list[dict[str, Any]], path: Path) -> None:
    accepted = sum(1 for row in rows if row["evaluation"]["accepted"])
    avg = sum(row["evaluation"]["score"] for row in rows) / max(1, len(rows))
    by_behavior = Counter(row["evaluation"]["expected_behavior"] for row in rows)
    lines = [
        "# Answer Quality Evaluation",
        "",
        f"- Questions: {len(rows)}",
        f"- Accepted: {accepted}/{len(rows)}",
        f"- Average score: {avg:.3f}",
        f"- By behavior: `{dict(sorted(by_behavior.items()))}`",
        "",
        "## Failures",
        "",
    ]
    failures = [row for row in rows if not row["evaluation"]["accepted"]]
    if not failures:
        lines.append("No failures.")
    for row in failures:
        ev = row["evaluation"]
        lines.extend(
            [
                f"### {ev['id']}",
                "",
                f"- Query: `{ev['query']}`",
                f"- Expected: `{ev['expected_behavior']}`",
                f"- Score: `{ev['score']}`",
                f"- Status: `{ev['status']}`",
                f"- Confidence: `{ev['confidence'].get('label')}`",
                f"- Failure reasons: `{ev['failure_reasons']}`",
                f"- Warnings: `{ev['warnings']}`",
                f"- Term hits: `{ev['term_hits']}`",
                f"- Citation term hits: `{ev['citation_term_hits']}`",
                f"- Issuer hits: `{ev['issuer_hits']}`",
                f"- Citation count: `{ev['citation_count']}`",
                f"- Answer chars: `{ev['answer_chars']}`",
                "",
            ]
        )

    lines.extend(["", "## All Questions", ""])
    for row in rows:
        ev = row["evaluation"]
        lines.extend(
            [
                f"### {ev['id']}",
                "",
                f"- Accepted: `{ev['accepted']}`",
                f"- Score: `{ev['score']}`",
                f"- Status: `{ev['status']}`",
                f"- Citation count: `{ev['citation_count']}`",
                f"- Failure reasons: `{ev['failure_reasons']}`",
                f"- Warnings: `{ev['warnings']}`",
                "",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def cmd_eval_answer_quality(args: argparse.Namespace) -> None:
    quality_path = Path(args.quality_file) if args.quality_file else ANSWER_QUALITY_QUESTIONS_PATH
    specs = load_gold_questions(quality_path)
    if args.limit:
        specs = specs[: args.limit]
    rows = []
    for index, spec in enumerate(specs, start=1):
        if args.progress:
            print(f"Evaluating answer quality {index}/{len(specs)}: {spec.get('id')}", flush=True)
        answer = build_answer(
            spec["query"],
            max_searches=args.max_searches,
            limit=args.result_limit,
            per_document_limit=args.per_document_limit,
            max_documents=args.max_documents,
            max_citations_per_document=args.max_citations_per_document,
        )
        evaluation = evaluate_answer_quality(spec, answer)
        row = {"spec": spec, "evaluation": evaluation}
        if args.include_answers:
            row["answer"] = answer
        rows.append(row)

    REPORTS_DIR.mkdir(exist_ok=True)
    prefix = args.report_prefix or "answer_quality_eval"
    md_path = REPORTS_DIR / f"{prefix}.md"
    json_path = REPORTS_DIR / f"{prefix}.json"
    write_answer_quality_report(rows, md_path)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    accepted = sum(1 for row in rows if row["evaluation"]["accepted"])
    avg = sum(row["evaluation"]["score"] for row in rows) / max(1, len(rows))
    print(f"Wrote {md_path.relative_to(ROOT)}")
    print(f"Wrote {json_path.relative_to(ROOT)}")
    print(f"Accepted {accepted}/{len(rows)}; average score {avg:.3f}")
