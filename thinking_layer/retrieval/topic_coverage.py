from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..common.text import normalize_space
from ..config.heuristics import load_heuristic_config
from ..config.paths import REPORTS_DIR, ROOT
from .query_tools import contains_pattern, load_query_lexicon, unique_keep_order


def cross_regulator_config() -> dict[str, Any]:
    return load_heuristic_config("cross_regulator_confidence")


def lexicon_terms_for_plan(plan: dict[str, Any]) -> list[str]:
    lexicon = load_query_lexicon()
    config = (cross_regulator_config().get("coverage") or {})
    terms: list[str] = []
    entity_names = set(plan.get("entities") or [])
    topic_names = set(plan.get("topics") or [])
    for item in lexicon.get("entities", []):
        if item.get("name") in entity_names:
            terms.extend(item.get("exact_phrases") or [])
            terms.extend(item.get("patterns") or [])
            terms.extend(item.get("expansions") or [])
    if not terms:
        for item in lexicon.get("topics", []):
            if item.get("name") in topic_names:
                terms.extend(item.get("exact_phrases") or [])
                terms.extend(item.get("patterns") or [])
                terms.extend(item.get("expansions") or [])
    deduped = unique_keep_order([term for term in terms if term])
    generic_terms = {str(term).lower() for term in config.get("generic_adjacent_terms") or []}
    specific_terms = [term for term in deduped if term.lower() not in generic_terms]
    return specific_terms or deduped


def field_has_topic(value: str, terms: list[str]) -> list[str]:
    normalized = normalize_space(value)
    return [term for term in terms if contains_pattern(normalized, term)]


def item_topic_match(item: dict[str, Any], terms: list[str], config: dict[str, Any]) -> dict[str, Any]:
    citation = item.get("citation") or {}
    title = citation.get("document") or ""
    snippet = item.get("snippet") or ""
    section_type = item.get("section_type")
    title_hits = field_has_topic(title, terms)
    snippet_hits = field_has_topic(snippet, terms)
    definition_markers = config.get("definition_markers") or []
    definition_section_types = set(config.get("definition_section_types") or [])
    is_definition = section_type in definition_section_types and any(
        marker.lower() in snippet.lower() for marker in definition_markers
    )
    definition_hits = snippet_hits if is_definition else []
    direct = bool(title_hits or definition_hits)
    if not bool(config.get("direct_title_required_for_comparison", True)):
        direct = direct or bool(snippet_hits)
    return {
        "direct": direct,
        "title_hits": title_hits,
        "definition_hits": definition_hits,
        "snippet_hits": snippet_hits,
        "citation": citation.get("text"),
        "document": title,
        "section_type": section_type,
        "snippet": snippet,
    }


def is_cross_regulator_plan(plan: dict[str, Any], config: dict[str, Any]) -> bool:
    issuers = [issuer for issuer in plan.get("issuers", []) if issuer]
    if len(set(issuers)) < int(config.get("min_issuers", 2)):
        return False
    intents = set(plan.get("intents") or [])
    comparison_intents = set(config.get("comparison_intents") or [])
    return bool(intents & comparison_intents)


def evaluate_cross_regulator_topic_coverage(pack: dict[str, Any]) -> dict[str, Any]:
    config = (cross_regulator_config().get("coverage") or {})
    plan = pack.get("plan") or {}
    issuers = unique_keep_order([issuer for issuer in plan.get("issuers", []) if issuer])
    terms = lexicon_terms_for_plan(plan)
    enabled = bool(config.get("enabled", True))
    applies = enabled and is_cross_regulator_plan(plan, config) and bool(terms)
    issuer_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for doc in pack.get("documents") or []:
        issuer = doc.get("issuer")
        if issuer in issuers:
            issuer_rows[issuer].extend(doc.get("citations") or [])

    by_issuer: dict[str, dict[str, Any]] = {}
    for issuer in issuers:
        matches = [item_topic_match(item, terms, config) for item in issuer_rows.get(issuer, [])]
        direct_matches = [match for match in matches if match["direct"]]
        adjacent_matches = [match for match in matches if match["snippet_hits"] and not match["direct"]]
        if direct_matches:
            label = str(config.get("direct_label", "direct"))
        elif adjacent_matches:
            label = str(config.get("adjacent_only_label", "adjacent_only"))
        else:
            label = str(config.get("missing_label", "missing"))
        by_issuer[issuer] = {
            "label": label,
            "direct": bool(direct_matches),
            "direct_matches": direct_matches[:3],
            "adjacent_matches": adjacent_matches[:3],
            "evidence_count": len(matches),
        }

    missing_direct_issuers = [issuer for issuer, payload in by_issuer.items() if not payload["direct"]]
    return {
        "applies": applies,
        "terms": terms,
        "issuers": issuers,
        "by_issuer": by_issuer,
        "missing_direct_issuers": missing_direct_issuers if applies else [],
        "downgrade_required": applies and bool(missing_direct_issuers),
        "downgrade_label": config.get("downgrade_label", "partial"),
        "downgrade_reason": config.get("downgrade_reason", "cross_regulator_missing_direct_topic_coverage"),
        "policy": {
            "direct_title_required_for_comparison": config.get("direct_title_required_for_comparison", True),
            "snippet_only_counts_as_adjacent": bool(config.get("direct_title_required_for_comparison", True)),
        },
    }


def apply_cross_regulator_confidence_gate(pack: dict[str, Any]) -> dict[str, Any]:
    coverage = evaluate_cross_regulator_topic_coverage(pack)
    pack["topic_coverage"] = coverage
    if not coverage.get("downgrade_required"):
        return pack
    confidence = dict(pack.get("confidence") or {})
    previous_label = confidence.get("label")
    confidence["label"] = coverage.get("downgrade_label") or "partial"
    confidence["must_say_not_found"] = False
    reasons = list(confidence.get("reasons") or [])
    reasons.append(str(coverage.get("downgrade_reason")))
    reasons.append(f"missing_direct_issuers={coverage.get('missing_direct_issuers')}")
    reasons.append(f"topic_terms={coverage.get('terms')}")
    confidence["reasons"] = reasons
    confidence["previous_label"] = previous_label
    pack["confidence"] = confidence
    return pack


def write_cross_regulator_coverage_audit(rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        "# Cross-Regulator Coverage Audit",
        "",
        "This report checks whether each requested issuer has direct topic-bearing evidence.",
        "For comparison/list-regulation questions, snippet-only mentions are treated as adjacent unless the title or definition block directly carries the topic.",
        "",
    ]
    for row in rows:
        coverage = row["coverage"]
        lines.extend(
            [
                f"## {row['query']}",
                "",
                f"- Confidence: `{row['confidence'].get('label')}` (previous `{row['confidence'].get('previous_label')}`)",
                f"- Applies: `{coverage.get('applies')}`",
                f"- Terms: `{coverage.get('terms')}`",
                f"- Missing direct issuers: `{coverage.get('missing_direct_issuers')}`",
                "",
            ]
        )
        for issuer, payload in (coverage.get("by_issuer") or {}).items():
            lines.extend(
                [
                    f"### `{issuer}`",
                    "",
                    f"- Label: `{payload.get('label')}`",
                    f"- Evidence count: `{payload.get('evidence_count')}`",
                    f"- Direct matches: `{len(payload.get('direct_matches') or [])}`",
                    f"- Adjacent matches: `{len(payload.get('adjacent_matches') or [])}`",
                    "",
                ]
            )
            for match in (payload.get("direct_matches") or [])[:2]:
                lines.append(f"- Direct: `{match.get('citation')}`")
            for match in (payload.get("adjacent_matches") or [])[:2]:
                lines.append(f"- Adjacent: `{match.get('citation')}`")
            lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def cmd_cross_regulator_coverage_audit(args: argparse.Namespace) -> None:
    from .evidence import build_evidence_pack

    config = cross_regulator_config()
    queries = args.query or (config.get("audit") or {}).get("queries") or []
    rows = []
    for query in queries:
        pack = build_evidence_pack(query, args.max_searches, args.limit, args.per_document_limit)
        rows.append({"query": query, "confidence": pack.get("confidence") or {}, "coverage": pack.get("topic_coverage") or {}})
    REPORTS_DIR.mkdir(exist_ok=True)
    md_path = REPORTS_DIR / "cross_regulator_coverage_audit.md"
    json_path = REPORTS_DIR / "cross_regulator_coverage_audit.json"
    write_cross_regulator_coverage_audit(rows, md_path)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {md_path.relative_to(ROOT)}")
    print(f"Wrote {json_path.relative_to(ROOT)}")
