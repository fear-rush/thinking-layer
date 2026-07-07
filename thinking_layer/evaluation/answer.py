from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from ..answer.composer import build_answer
from ..config.heuristics import heuristic_section
from ..config.paths import GOLD_QUESTIONS_PATH, REPORTS_DIR, ROOT
from .evidence import load_gold_questions, title_matches_expected

def evaluate_answer(spec: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    config = heuristic_section("evaluation_rubrics", "answer")
    expected_behavior = spec.get("expected_behavior") or "answerable"
    required_issuers = spec.get("required_issuers") or []
    expected_documents = spec.get("expected_documents") or []
    expected_document_mode = spec.get("expected_document_mode") or "any"
    documents_used = answer.get("documents_used") or []
    document_titles = [doc.get("document") or "" for doc in documents_used]
    issuer_hits = sorted({doc.get("issuer") for doc in documents_used if doc.get("issuer") in required_issuers})
    document_hits = [
        expected
        for expected in expected_documents
        if any(title_matches_expected(title, expected) for title in document_titles[: int(config.get("top_document_count", 8))])
    ]
    answer_text = answer.get("answer") or ""
    status = answer.get("status")
    confidence = answer.get("confidence") or {}
    citation_count = int(answer.get("citation_count") or 0)
    contains_not_found = "tidak ditemukan" in answer_text.lower()

    failure_reasons: list[str] = []
    if expected_behavior == "not_found":
        accepted = status == "not_found" and contains_not_found and citation_count == 0
        score = 1.0 if accepted else 0.0
        if status != "not_found":
            failure_reasons.append("expected not_found status")
        if not contains_not_found:
            failure_reasons.append("answer missing not-found language")
        if citation_count:
            failure_reasons.append("not-found answer should not cite evidence as support")
    else:
        issuer_score = len(issuer_hits) / max(1, len(required_issuers))
        if expected_document_mode == "all":
            document_score = len(document_hits) / max(1, len(expected_documents))
        else:
            document_score = 1.0 if not expected_documents or document_hits else 0.0
        citation_score = 1.0 if citation_count > 0 else 0.0
        status_score = (config.get("status_score") or {}).get(status, 0.0)
        confidence_score = (config.get("confidence_score") or {}).get(confidence.get("label"), 0.0)
        weights = config.get("weights") or {}
        score = (
            float(weights.get("document_score", 0.30)) * document_score
            + float(weights.get("issuer_score", 0.25)) * issuer_score
            + float(weights.get("citation_score", 0.20)) * citation_score
            + float(weights.get("status_score", 0.15)) * status_score
            + float(weights.get("confidence_score", 0.10)) * confidence_score
        )
        threshold = float(config.get("partial_threshold", 0.72)) if expected_behavior == "partial" else float(config.get("answerable_threshold", 0.82))
        accepted = score >= threshold and status != "not_found"
        if document_score < 1.0:
            failure_reasons.append("missing expected document in answer")
        if issuer_score < 1.0:
            failure_reasons.append("missing required issuer in answer")
        if citation_count == 0:
            failure_reasons.append("answer has no citations")
        if status == "not_found":
            failure_reasons.append("unexpected not_found answer")

    return {
        "id": spec.get("id"),
        "query": spec.get("query"),
        "expected_behavior": expected_behavior,
        "score": round(score, 3),
        "accepted": accepted,
        "status": status,
        "confidence": confidence,
        "citation_count": citation_count,
        "required_issuers": required_issuers,
        "issuer_hits": issuer_hits,
        "expected_documents": expected_documents,
        "expected_document_mode": expected_document_mode,
        "document_hits": document_hits,
        "top_documents": [
            {
                "document": doc.get("document"),
                "issuer": doc.get("issuer"),
                "source_priority": doc.get("source_priority"),
                "file_role": doc.get("file_role"),
            }
            for doc in documents_used[: int(config.get("top_report_documents", 5))]
        ],
        "failure_reasons": failure_reasons,
        "notes": spec.get("notes"),
    }

def write_answer_eval_report(rows: list[dict[str, Any]], path: Path) -> None:
    accepted = sum(1 for row in rows if row["evaluation"]["accepted"])
    avg = sum(row["evaluation"]["score"] for row in rows) / max(1, len(rows))
    by_behavior = Counter(row["evaluation"]["expected_behavior"] for row in rows)
    lines = [
        "# Answer Evaluation",
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
                f"- Failure reasons: `{ev['failure_reasons']}`",
                f"- Document hits: `{ev['document_hits']}`",
                f"- Issuer hits: `{ev['issuer_hits']}`",
                f"- Citation count: `{ev['citation_count']}`",
                "",
            ]
        )
        for doc in ev["top_documents"]:
            lines.append(f"  - `{doc['issuer']}` `{doc['source_priority']}` `{doc['file_role']}` - {doc['document']}")
        lines.append("")

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
                f"- Confidence: `{ev['confidence'].get('label')}`",
                f"- Citation count: `{ev['citation_count']}`",
                f"- Document hits: `{ev['document_hits']}`",
                f"- Issuer hits: `{ev['issuer_hits']}`",
                "",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def cmd_eval_answer(args: argparse.Namespace) -> None:
    gold_path = Path(args.gold_file) if args.gold_file else GOLD_QUESTIONS_PATH
    specs = load_gold_questions(gold_path)
    if args.limit:
        specs = specs[: args.limit]
    rows = []
    for index, spec in enumerate(specs, start=1):
        if args.progress:
            print(f"Evaluating answer {index}/{len(specs)}: {spec.get('id')}", flush=True)
        answer = build_answer(
            spec["query"],
            max_searches=args.max_searches,
            limit=args.result_limit,
            per_document_limit=args.per_document_limit,
            max_documents=args.max_documents,
            max_citations_per_document=args.max_citations_per_document,
        )
        evaluation = evaluate_answer(spec, answer)
        row = {
            "spec": spec,
            "evaluation": evaluation,
        }
        if args.include_answers:
            row["answer"] = answer
        rows.append(row)

    REPORTS_DIR.mkdir(exist_ok=True)
    prefix = args.report_prefix or "answer_eval"
    md_path = REPORTS_DIR / f"{prefix}.md"
    json_path = REPORTS_DIR / f"{prefix}.json"
    write_answer_eval_report(rows, md_path)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    accepted = sum(1 for row in rows if row["evaluation"]["accepted"])
    avg = sum(row["evaluation"]["score"] for row in rows) / max(1, len(rows))
    print(f"Wrote {md_path.relative_to(ROOT)}")
    print(f"Wrote {json_path.relative_to(ROOT)}")
    print(f"Accepted {accepted}/{len(rows)}; average score {avg:.3f}")
