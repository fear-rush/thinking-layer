from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..answer.composer import build_answer
from ..answer.quality import evaluate_answer_quality, write_answer_quality_report
from ..config.paths import REPORTS_DIR, ROOT
from ..retrieval.evidence import build_evidence_pack
from .answer import evaluate_answer, write_answer_eval_report
from .evidence import evaluate_evidence_pack, load_gold_questions, write_evidence_eval_report

def load_holdout_specs(path: Path, label: str, allow_template: bool) -> list[dict[str, Any]]:
    specs = load_gold_questions(path)
    template_ids = [spec.get("id") for spec in specs if "replace_me" in str(spec.get("id") or "")]
    if template_ids and not allow_template:
        raise SystemExit(
            f"{label} still contains template IDs: {template_ids}. "
            "Replace placeholders with reviewer-owned questions, or pass --allow-template for a dry run."
        )
    return specs

def summarize_eval_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = sum(1 for row in rows if row["evaluation"]["accepted"])
    avg = sum(row["evaluation"]["score"] for row in rows) / max(1, len(rows))
    failures = [
        {
            "id": row["evaluation"].get("id"),
            "query": row["evaluation"].get("query"),
            "score": row["evaluation"].get("score"),
            "failure_reasons": row["evaluation"].get("failure_reasons"),
        }
        for row in rows
        if not row["evaluation"]["accepted"]
    ]
    return {
        "accepted": accepted,
        "total": len(rows),
        "average_score": round(avg, 3),
        "failures": failures,
    }

def write_external_holdout_review_checklist(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# External Holdout Review Checklist",
        "",
        f"- Run timestamp: `{manifest['created_at']}`",
        f"- Gold file: `{manifest['gold_file']}`",
        f"- Quality file: `{manifest['quality_file']}`",
        "",
        "## Pre-Run Integrity",
        "",
        "- [ ] Questions were written before running this validation.",
        "- [ ] Reviewer did not inspect retrieval results while writing expected labels.",
        "- [ ] Questions are not copied from `resources/gold_questions.json`, `resources/holdout_questions.internal.json`, or prior failure reports.",
        "- [ ] At least one BI-only, OJK-only, cross-regulator, partial, and not-found question is included where relevant.",
        "- [ ] Expected documents use title substrings, not exact snippets from retrieved answers.",
        "",
        "## Post-Run Triage",
        "",
        "- [ ] Each failure is classified as retrieval, citation extraction, answer composer, answer quality, or gold-label issue.",
        "- [ ] Any code or label change after seeing failures is logged with rationale.",
        "- [ ] Metrics are reported with exact file paths and dates.",
        "- [ ] This run is not called blind again after code/label tuning against it.",
        "",
        "## Results",
        "",
        f"- Evidence: `{manifest['results']['evidence']['accepted']}/{manifest['results']['evidence']['total']}`, average `{manifest['results']['evidence']['average_score']}`.",
        f"- Answer: `{manifest['results']['answer']['accepted']}/{manifest['results']['answer']['total']}`, average `{manifest['results']['answer']['average_score']}`.",
        f"- Answer quality: `{manifest['results']['answer_quality']['accepted']}/{manifest['results']['answer_quality']['total']}`, average `{manifest['results']['answer_quality']['average_score']}`.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def cmd_validate_holdout(args: argparse.Namespace) -> None:
    gold_path = Path(args.gold_file)
    quality_path = Path(args.quality_file)
    if not gold_path.exists():
        raise SystemExit(f"Missing external gold file: {gold_path}")
    if not quality_path.exists():
        raise SystemExit(f"Missing external quality file: {quality_path}")

    gold_specs = load_holdout_specs(gold_path, "gold file", args.allow_template)
    quality_specs = load_holdout_specs(quality_path, "quality file", args.allow_template)
    REPORTS_DIR.mkdir(exist_ok=True)

    evidence_rows = []
    for index, spec in enumerate(gold_specs, start=1):
        if args.progress:
            print(f"External evidence {index}/{len(gold_specs)}: {spec.get('id')}", flush=True)
        pack = build_evidence_pack(spec["query"], args.max_searches, args.result_limit, args.per_document_limit)
        evidence_rows.append({"report_kind": "external_holdout", "spec": spec, "evaluation": evaluate_evidence_pack(spec, pack), "pack": None})

    answer_rows = []
    for index, spec in enumerate(gold_specs, start=1):
        if args.progress:
            print(f"External answer {index}/{len(gold_specs)}: {spec.get('id')}", flush=True)
        answer = build_answer(
            spec["query"],
            max_searches=args.max_searches,
            limit=args.result_limit,
            per_document_limit=args.per_document_limit,
            max_documents=args.max_documents,
            max_citations_per_document=args.max_citations_per_document,
        )
        answer_rows.append({"spec": spec, "evaluation": evaluate_answer(spec, answer)})

    quality_rows = []
    for index, spec in enumerate(quality_specs, start=1):
        if args.progress:
            print(f"External answer quality {index}/{len(quality_specs)}: {spec.get('id')}", flush=True)
        answer = build_answer(
            spec["query"],
            max_searches=args.max_searches,
            limit=args.result_limit,
            per_document_limit=args.per_document_limit,
            max_documents=args.max_documents,
            max_citations_per_document=args.max_citations_per_document,
        )
        quality_rows.append({"spec": spec, "evaluation": evaluate_answer_quality(spec, answer)})

    prefix = args.report_prefix
    evidence_md = REPORTS_DIR / f"{prefix}_evidence.md"
    evidence_json = REPORTS_DIR / f"{prefix}_evidence.json"
    answer_md = REPORTS_DIR / f"{prefix}_answer.md"
    answer_json = REPORTS_DIR / f"{prefix}_answer.json"
    quality_md = REPORTS_DIR / f"{prefix}_answer_quality.md"
    quality_json = REPORTS_DIR / f"{prefix}_answer_quality.json"
    manifest_json = REPORTS_DIR / f"{prefix}_manifest.json"
    checklist_md = REPORTS_DIR / f"{prefix}_review_checklist.md"

    write_evidence_eval_report(evidence_rows, evidence_md)
    evidence_json.write_text(json.dumps(evidence_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_answer_eval_report(answer_rows, answer_md)
    answer_json.write_text(json.dumps(answer_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_answer_quality_report(quality_rows, quality_md)
    quality_json.write_text(json.dumps(quality_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "report_prefix": prefix,
        "gold_file": str(gold_path),
        "quality_file": str(quality_path),
        "allow_template": args.allow_template,
        "parameters": {
            "max_searches": args.max_searches,
            "result_limit": args.result_limit,
            "per_document_limit": args.per_document_limit,
            "max_documents": args.max_documents,
            "max_citations_per_document": args.max_citations_per_document,
        },
        "reports": {
            "evidence_md": str(evidence_md.relative_to(ROOT)),
            "evidence_json": str(evidence_json.relative_to(ROOT)),
            "answer_md": str(answer_md.relative_to(ROOT)),
            "answer_json": str(answer_json.relative_to(ROOT)),
            "answer_quality_md": str(quality_md.relative_to(ROOT)),
            "answer_quality_json": str(quality_json.relative_to(ROOT)),
            "review_checklist_md": str(checklist_md.relative_to(ROOT)),
        },
        "results": {
            "evidence": summarize_eval_rows(evidence_rows),
            "answer": summarize_eval_rows(answer_rows),
            "answer_quality": summarize_eval_rows(quality_rows),
        },
    }
    manifest_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_external_holdout_review_checklist(checklist_md, manifest)

    print(f"Wrote {evidence_md.relative_to(ROOT)}")
    print(f"Wrote {answer_md.relative_to(ROOT)}")
    print(f"Wrote {quality_md.relative_to(ROOT)}")
    print(f"Wrote {manifest_json.relative_to(ROOT)}")
    print(f"Wrote {checklist_md.relative_to(ROOT)}")
    print(
        "External holdout summary: "
        f"evidence {manifest['results']['evidence']['accepted']}/{manifest['results']['evidence']['total']}, "
        f"answer {manifest['results']['answer']['accepted']}/{manifest['results']['answer']['total']}, "
        f"quality {manifest['results']['answer_quality']['accepted']}/{manifest['results']['answer_quality']['total']}."
    )
