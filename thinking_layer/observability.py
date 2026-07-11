from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .answer.composer import build_answer
from .common.text import slugify
from .config.paths import REPORTS_DIR, ROOT


def _top_evidence_summary(item: dict[str, Any]) -> dict[str, Any]:
    citation = item.get("citation") or {}
    return {
        "file_id": item.get("file_id"),
        "block_id": item.get("block_id"),
        "document": citation.get("document"),
        "issuer": item.get("issuer"),
        "source_priority": item.get("source_priority"),
        "file_role": item.get("file_role"),
        "regulation_version_key": item.get("regulation_version_key"),
        "regulation_series_key": item.get("regulation_series_key"),
        "lifecycle_status": item.get("lifecycle_status"),
        "is_current": item.get("is_current"),
        "effective_date": item.get("effective_date"),
        "page": citation.get("page"),
        "pasal": citation.get("pasal"),
        "ayat": citation.get("ayat"),
        "citation_quality": citation.get("quality"),
        "support_score": item.get("support_score"),
        "planned_query": item.get("planned_query"),
        "plan_reason": item.get("plan_reason"),
        "matched_exact_phrases": item.get("matched_exact_phrases") or [],
        "extraction_flags": item.get("extraction_flags") or [],
        "snippet": (item.get("snippet") or "")[:320],
    }


def trace_from_answer(answer: dict[str, Any], *, generated_at: str | None = None, top_evidence: int = 10) -> dict[str, Any]:
    pack = answer.get("evidence_pack") or {}
    plan = pack.get("plan") or {}
    items = pack.get("ungrouped_evidence") or []
    confidence = pack.get("confidence") or {}
    citation_quality_counts = Counter(
        (item.get("citation") or {}).get("quality") or "unknown" for item in items
    )
    extraction_flag_counts = Counter(
        flag for item in items for flag in (item.get("extraction_flags") or [])
    )
    issuer_counts = Counter(item.get("issuer") or "unknown" for item in items)
    primary_count = sum(1 for item in items if item.get("is_primary"))
    status = answer.get("status")
    refused = status == "not_found" or bool(confidence.get("must_say_not_found"))

    return {
        "schema_version": 1,
        "generated_at_utc": generated_at or datetime.now(timezone.utc).isoformat(),
        "query": pack.get("query"),
        "query_plan": {
            "intents": plan.get("intents") or [],
            "issuers": plan.get("issuers") or [],
            "entities": plan.get("entities") or [],
            "topics": plan.get("topics") or [],
            "search_count": len(plan.get("searches") or []),
            "searches": plan.get("searches") or [],
        },
        "retrieval": {
            "evidence_count": len(items),
            "document_count": len(pack.get("documents") or []),
            "primary_evidence_rate": round(primary_count / max(1, len(items)), 3),
            "issuer_counts": dict(sorted(issuer_counts.items())),
            "citation_quality_counts": dict(sorted(citation_quality_counts.items())),
            "extraction_flag_counts": dict(sorted(extraction_flag_counts.items())),
            "top_evidence": [_top_evidence_summary(item) for item in items[:top_evidence]],
        },
        "decision": {
            "status": status,
            "confidence": confidence,
            "refused": refused,
            "refusal_reasons": confidence.get("reasons") or [] if refused else [],
            "topic_coverage": pack.get("topic_coverage"),
        },
        "answer": {
            "citation_count": answer.get("citation_count", 0),
            "document_count": len(answer.get("documents_used") or []),
            "answer_chars": len(answer.get("answer") or ""),
            "composer": answer.get("composer"),
        },
    }


def build_query_trace(
    query: str,
    *,
    max_searches: int = 8,
    limit: int = 12,
    per_document_limit: int = 3,
    max_documents: int = 6,
    max_citations_per_document: int = 2,
    top_evidence: int = 10,
) -> dict[str, Any]:
    answer = build_answer(
        query,
        max_searches=max_searches,
        limit=limit,
        per_document_limit=per_document_limit,
        max_documents=max_documents,
        max_citations_per_document=max_citations_per_document,
    )
    return trace_from_answer(answer, top_evidence=top_evidence)


def format_query_trace(trace: dict[str, Any]) -> str:
    plan = trace["query_plan"]
    retrieval = trace["retrieval"]
    decision = trace["decision"]
    answer = trace["answer"]
    lines = [
        "# Query Trace",
        "",
        f"- Query: `{trace['query']}`",
        f"- Intents: `{plan['intents']}`",
        f"- Issuers: `{plan['issuers']}`",
        f"- Topics: `{plan['topics']}`",
        f"- Planned searches: `{plan['search_count']}`",
        f"- Evidence items: `{retrieval['evidence_count']}`",
        f"- Documents: `{retrieval['document_count']}`",
        f"- Primary evidence rate: `{retrieval['primary_evidence_rate']}`",
        f"- Status: `{decision['status']}`",
        f"- Confidence: `{(decision.get('confidence') or {}).get('label')}`",
        f"- Refused: `{decision['refused']}`",
        f"- Citations: `{answer['citation_count']}`",
        f"- Answer characters: `{answer['answer_chars']}`",
        "",
        "## Citation Quality",
        "",
        f"`{retrieval['citation_quality_counts']}`",
        "",
        "## Refusal Reasons",
        "",
    ]
    lines.extend(f"- {reason}" for reason in decision["refusal_reasons"] or ["None."])
    return "\n".join(lines) + "\n"


def cmd_trace_query(args: argparse.Namespace) -> None:
    trace = build_query_trace(
        args.query,
        max_searches=args.max_searches,
        limit=args.limit,
        per_document_limit=args.per_document_limit,
        max_documents=args.max_documents,
        max_citations_per_document=args.max_citations_per_document,
        top_evidence=args.top_evidence,
    )
    print(format_query_trace(trace))
    if args.write_report:
        REPORTS_DIR.mkdir(exist_ok=True)
        stem = slugify(args.query)[:80] or "query"
        path = Path(args.output) if args.output else REPORTS_DIR / f"query_trace_{stem}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        display_path = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        print(f"Wrote {display_path}")
