from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from ..config.heuristics import heuristic_section
from ..config.paths import GOLD_QUESTIONS_PATH, REPORTS_DIR, ROOT
from ..retrieval.evidence import build_evidence_pack

def load_gold_questions(path: Path = GOLD_QUESTIONS_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Missing {path.relative_to(ROOT)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"{path.relative_to(ROOT)} must contain a JSON array")
    return data

def title_matches_expected(title: str, expected: str) -> bool:
    title_l = title.lower()
    parts = [part.strip().lower() for part in expected.split("|") if part.strip()]
    if len(parts) > 1:
        return all(part in title_l for part in parts)
    return expected.lower() in title_l

def evaluate_evidence_pack(spec: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    config = heuristic_section("evaluation_rubrics", "evidence")
    expected_behavior = spec.get("expected_behavior") or "answerable"
    expected_documents = spec.get("expected_documents") or []
    expected_document_mode = spec.get("expected_document_mode") or "any"
    required_issuers = spec.get("required_issuers") or []
    documents = pack.get("documents") or []
    document_titles = [doc.get("document") or "" for doc in documents]
    issuer_hits = sorted({doc.get("issuer") for doc in documents if doc.get("issuer") in required_issuers})
    document_hits = [
        expected
        for expected in expected_documents
        if any(title_matches_expected(title, expected) for title in document_titles[: int(config.get("top_document_count", 8))])
    ]
    confidence = pack["confidence"]

    if expected_behavior == "not_found":
        accepted = bool(confidence.get("must_say_not_found"))
        score = 1.0 if accepted else 0.0
        failure_reasons = [] if accepted else ["expected not_found but evidence did not require refusal"]
    else:
        issuer_score = len(issuer_hits) / max(1, len(required_issuers))
        if expected_document_mode == "all":
            document_score = len(document_hits) / max(1, len(expected_documents))
            missing_document = document_score < 1.0
        else:
            document_score = 1.0 if not expected_documents or document_hits else 0.0
            missing_document = bool(expected_documents and not document_hits)
        confidence_score = (config.get("confidence_score") or {}).get(confidence.get("label"), 0.0)
        citation_score = 0.0
        top_items = pack.get("ungrouped_evidence") or []
        if top_items:
            top = top_items[: int(config.get("top_citation_count", 5))]
            page_rate = sum(1 for item in top if item.get("has_page")) / len(top)
            primary_rate = sum(1 for item in top if item.get("is_primary")) / len(top)
            citation_score = (page_rate + primary_rate) / 2
        weights = config.get("weights") or {}
        score = (
            float(weights.get("document_score", 0.40)) * document_score
            + float(weights.get("issuer_score", 0.25)) * issuer_score
            + float(weights.get("confidence_score", 0.20)) * confidence_score
            + float(weights.get("citation_score", 0.15)) * citation_score
        )
        threshold = float(config.get("partial_threshold", 0.72)) if expected_behavior == "partial" else float(config.get("answerable_threshold", 0.82))
        accepted = score >= threshold and not confidence.get("must_say_not_found")
        failure_reasons = []
        if missing_document:
            failure_reasons.append("missing expected document")
        if issuer_score < 1.0:
            failure_reasons.append("missing required issuer")
        if confidence.get("must_say_not_found"):
            failure_reasons.append("unexpected not_found flag")

    return {
        "id": spec.get("id"),
        "query": spec.get("query"),
        "expected_behavior": expected_behavior,
        "score": round(score, 3),
        "accepted": accepted,
        "confidence": confidence,
        "required_issuers": required_issuers,
        "issuer_hits": issuer_hits,
        "expected_documents": expected_documents,
        "expected_document_mode": expected_document_mode,
        "document_hits": document_hits,
        "top_documents": [
            {
                "document": doc.get("document"),
                "issuer": doc.get("issuer"),
                "file_role": doc.get("file_role"),
                "top_score": doc.get("top_score"),
            }
            for doc in documents[:5]
        ],
        "failure_reasons": failure_reasons,
        "notes": spec.get("notes"),
    }

def write_evidence_eval_report(rows: list[dict[str, Any]], path: Path) -> None:
    accepted = sum(1 for row in rows if row["evaluation"]["accepted"])
    avg = sum(row["evaluation"]["score"] for row in rows) / max(1, len(rows))
    by_behavior = Counter(row["evaluation"]["expected_behavior"] for row in rows)
    lines = [
        "# Evidence Evaluation",
        "",
        f"- Questions: {len(rows)}",
        f"- Accepted: {accepted}/{len(rows)}",
        f"- Average score: {avg:.3f}",
        f"- By behavior: `{dict(sorted(by_behavior.items()))}`",
        f"- Report kind: `{rows[0].get('report_kind') if rows else 'unknown'}`",
        "",
    ]
    failures = [row for row in rows if not row["evaluation"]["accepted"]]
    lines.extend(["## Failures", ""])
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
                f"- Confidence: `{ev['confidence']['label']}` / not_found `{ev['confidence']['must_say_not_found']}`",
                f"- Failure reasons: `{ev['failure_reasons']}`",
                f"- Document hits: `{ev['document_hits']}`",
                f"- Issuer hits: `{ev['issuer_hits']}`",
                "- Top documents:",
            ]
        )
        for doc in ev["top_documents"]:
            lines.append(f"  - `{doc['issuer']}` `{doc['file_role']}` - {doc['document']}")
        lines.append("")

    lines.extend(["## All Questions", ""])
    for row in rows:
        ev = row["evaluation"]
        lines.extend(
            [
                f"### {ev['id']}",
                "",
                f"- Accepted: `{ev['accepted']}`",
                f"- Score: `{ev['score']}`",
                f"- Expected: `{ev['expected_behavior']}`",
                f"- Confidence: `{ev['confidence']['label']}` / not_found `{ev['confidence']['must_say_not_found']}`",
                f"- Document hits: `{ev['document_hits']}`",
                f"- Issuer hits: `{ev['issuer_hits']}`",
                "",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def cmd_eval_evidence(args: argparse.Namespace) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    gold_path = Path(args.gold_file) if args.gold_file else GOLD_QUESTIONS_PATH
    report_kind = "holdout" if args.gold_file else "development"
    specs = load_gold_questions(gold_path)
    if args.limit:
        specs = specs[: args.limit]
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(specs, start=1):
        if args.progress:
            print(f"Evaluating {index}/{len(specs)}: {spec.get('id')}", flush=True)
        pack = build_evidence_pack(spec["query"], args.max_searches, args.result_limit, args.per_document_limit)
        evaluation = evaluate_evidence_pack(spec, pack)
        rows.append({"report_kind": report_kind, "spec": spec, "evaluation": evaluation, "pack": pack if args.include_packs else None})

    prefix = args.report_prefix or ("holdout_eval" if args.gold_file else "evidence_eval")
    md_path = REPORTS_DIR / f"{prefix}.md"
    json_path = REPORTS_DIR / f"{prefix}.json"
    write_evidence_eval_report(rows, md_path)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    accepted = sum(1 for row in rows if row["evaluation"]["accepted"])
    avg = sum(row["evaluation"]["score"] for row in rows) / max(1, len(rows))
    print(f"Wrote {md_path.relative_to(ROOT)}")
    print(f"Wrote {json_path.relative_to(ROOT)}")
    print(f"Accepted {accepted}/{len(rows)}; average score {avg:.3f}")
    if not args.gold_file:
        print("Note: this is the development gold set, not a blind holdout.")
