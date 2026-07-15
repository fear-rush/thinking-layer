from __future__ import annotations

import argparse
import json
from collections import defaultdict
from typing import Any

from ..config.heuristics import heuristic_section
from ..corpus.citations import citation_quality_for_block, citation_text_for_block, section_type_for_block, source_priority_for_role
from ..corpus.quality import extraction_issue_flags
from ..indexing.lexical import get_search_index, snippet
from ..indexing.sqlite import sqlite_index_is_current
from ..config.paths import REPORTS_DIR, ROOT
from .planning import build_query_plan
from .query_tools import load_stopwords, query_overlap_score, tokenize_with_stopwords
from .search import execute_query_plan, row_matches_legal_constraints
from .topic_coverage import apply_cross_regulator_confidence_gate
from ..common.text import slugify
from ..answer.alignment import answer_alignment, has_lifecycle_provenance, is_lifecycle_query

def citation_dict(row: dict[str, Any]) -> dict[str, Any]:
    citation = row.get("citation") or {}
    source_block_ids = row["source_block_ids"]
    return {
        "document": citation.get("document") or row.get("document_title"),
        "page": citation.get("page") or row.get("page_start"),
        "page_start": citation.get("page_start") or row.get("page_start"),
        "page_end": citation.get("page_end") or row.get("page_end") or row.get("page_start"),
        "pasal": citation.get("pasal") or row.get("pasal"),
        "ayat": citation.get("ayat") or row.get("ayat"),
        "huruf": citation.get("huruf") or row.get("huruf"),
        "text": citation.get("text") or citation_text_for_block(row),
        "quality": citation.get("quality") or row.get("citation_quality") or citation_quality_for_block(row),
        "source_block_ids": [str(value) for value in source_block_ids if value],
        "unit_path": row["unit_path"],
        "legal_path": row["legal_path"],
        "anchors": row["anchors"],
        "source_spans": row["source_spans"],
    }

def phrase_anchored_in_query(phrase: str, query: str) -> bool:
    query_tokens = tokenize_with_stopwords(query, load_stopwords())
    phrase_tokens = tokenize_with_stopwords(phrase, load_stopwords())
    if not phrase_tokens:
        return False
    acronym = "".join(token[0] for token in phrase_tokens if token)
    if acronym and acronym in query_tokens:
        return True
    return all(
        any(phrase_token in query_token or query_token in phrase_token for query_token in query_tokens)
        for phrase_token in phrase_tokens
    )

def query_allows_table_evidence(query: str, config: dict[str, Any]) -> bool:
    query_l = query.lower()
    return any(term in query_l for term in config.get("query_allows_table_terms") or [])

def extraction_quality_multiplier(query: str, row: dict[str, Any], config: dict[str, Any]) -> tuple[float, list[str]]:
    flags = extraction_issue_flags(row)
    multipliers = config.get("extraction_quality_multipliers") or {}
    allows_table = query_allows_table_evidence(query, config)
    multiplier = 1.0
    for flag in flags:
        if flag == "markdown_table_artifact" and allows_table:
            continue
        multiplier *= float(multipliers.get(flag, 1.0))
    return multiplier, flags


def evidence_item(query: str, row: dict[str, Any]) -> dict[str, Any]:
    config = heuristic_section("evidence_confidence", "item_support")
    citation = citation_dict(row)
    title = citation.get("document") or ""
    text = row.get("text") or ""
    matched_exact_phrases = [
        phrase
        for phrase in row.get("_matched_exact_phrases") or []
        if phrase_anchored_in_query(phrase, query)
    ]
    title_overlap = query_overlap_score(query, title)
    snippet_overlap = query_overlap_score(query, text[: int(config.get("snippet_overlap_chars", 1000))])
    lexical_support = min(
        float(config.get("max_lexical_support", 1.0)),
        (title_overlap * float(config.get("title_overlap_weight", 0.16)))
        + (snippet_overlap * float(config.get("snippet_overlap_weight", 0.10)))
        + (len(matched_exact_phrases) * float(config.get("matched_exact_phrase_weight", 0.20))),
    )
    quality_multiplier, extraction_flags = extraction_quality_multiplier(query, row, config)
    exact_phrase_multiplier = 1.0 + (
        len(matched_exact_phrases)
        * float(config.get("exact_phrase_score_multiplier_per_phrase", 0.0))
    )
    support_score = (
        float(row.get("_score") or 0)
        * (float(config.get("support_score_base_multiplier", 0.75)) + lexical_support)
        * quality_multiplier
        * exact_phrase_multiplier
    )
    return {
        "file_id": row.get("file_id"),
        "block_id": row.get("block_id"),
        "page_start": row.get("page_start"),
        "pasal": row.get("pasal"),
        "ayat": row.get("ayat"),
        "huruf": row.get("huruf"),
        "score": round(float(row.get("_score") or 0), 3),
        "support_score": round(support_score, 3),
        "bm25_score": round(float(row.get("_bm25_score") or row.get("_score") or 0), 3),
        "issuer": row.get("issuer"),
        "source": row.get("source"),
        "source_priority": row.get("source_priority") or source_priority_for_role(row.get("file_role")),
        "file_role": row.get("file_role"),
        "regulation_version_key": row.get("regulation_version_key") or row.get("canonical_id"),
        "regulation_series_key": row.get("regulation_series_key"),
        "regulation_type": row.get("regulation_type"),
        "number": row.get("number"),
        "year": row.get("year"),
        "issued_date": row.get("issued_date"),
        "effective_date": row.get("effective_date"),
        "repeal_date": row.get("repeal_date"),
        "lifecycle_status": row.get("lifecycle_status"),
        "is_current": row.get("is_current"),
        "supersedes": row.get("supersedes") or [],
        "amends": row.get("amends") or [],
        "citation": citation,
        "citation_quality": citation.get("quality"),
        "section_type": row.get("section_type") or section_type_for_block(row),
        "block_type": row.get("block_type"),
        "citation_admission": row.get("citation_admission"),
        "chunk_schema_version": row.get("chunk_schema_version"),
        "node_id": row.get("node_id"),
        "parent_id": row.get("parent_id"),
        "previous_id": row.get("previous_id"),
        "source_block_ids": citation["source_block_ids"],
        "unit_path": citation["unit_path"],
        "assembled_text": row.get("assembled_text") or row.get("retrieval_text"),
        "legal_path": citation.get("legal_path"),
        "anchors": citation.get("anchors") or [],
        "source_spans": citation.get("source_spans") or [],
        "legal_unit": row.get("legal_unit"),
        "planned_query": row.get("_planned_query"),
        "plan_reason": row.get("_plan_reason"),
        "matched_exact_phrases": matched_exact_phrases,
        "title_overlap": round(title_overlap, 3),
        "snippet_overlap": round(snippet_overlap, 3),
        "lexical_support": round(lexical_support, 3),
        "extraction_quality_multiplier": round(quality_multiplier, 3),
        "exact_phrase_multiplier": round(exact_phrase_multiplier, 3),
        "extraction_flags": extraction_flags,
        "text": text,
        "snippet": snippet(row.get("text") or "", query),
        "has_page": bool(citation.get("page")),
        "has_article": bool(citation.get("pasal")),
        "is_primary": (row.get("source_priority") or source_priority_for_role(row.get("file_role"))) == "primary",
    }

def query_requests_compound_answer(query: str) -> bool:
    query_l = query.casefold()
    return (
        " dan kapan " in query_l
        or ("psps" in query_l and "pspk" in query_l)
        or "klausula eksonerasi" in query_l
        or (
            "data" in query_l
            and any(term in query_l for term in ("pihak lain", "perusahaan lain"))
            and any(term in query_l for term in ("pemberian", "memberikan", "membagikan"))
        )
    )


def answer_alignment_threshold(query: str, plan: dict[str, Any]) -> float:
    if plan.get("ambiguity") or query_requests_compound_answer(query):
        return 0.25
    return 0.75


def evidence_confidence(items: list[dict[str, Any]], expected_issuers: list[str | None], plan: dict[str, Any], query: str) -> dict[str, Any]:
    config = heuristic_section("evidence_confidence", "confidence_score")
    if not items:
        return {
            "label": "not_found",
            "score": 0.0,
            "reasons": ["no evidence retrieved"],
            "must_say_not_found": True,
        }

    ambiguous = bool(plan.get("ambiguity"))
    alignment_threshold = answer_alignment_threshold(query, plan)
    alignments = [
        answer_alignment(
            query,
            item,
            minimum_distinctive_ratio=alignment_threshold,
            allow_missing_value=ambiguous or query_requests_compound_answer(query),
            allow_missing_predicate=query_requests_compound_answer(query),
        )
        for item in items
    ]
    aligned_items = [item for item, alignment in zip(items, alignments, strict=True) if alignment.accepted]
    if not aligned_items:
        reasons = ["no query-aligned evidence"]
        constraints = plan.get("legal_constraints") or {}
        if constraints and not all(row_matches_legal_constraints(item, constraints) for item in items):
            reasons.append("requested_legal_constraint_not_satisfied")
        reasons.extend(
            dict.fromkeys(reason for alignment in alignments for reason in alignment.reasons)
        )
        return {
            "label": "weak",
            "score": 0.0,
            "reasons": reasons,
            "must_say_not_found": True,
        }

    items = aligned_items
    if is_lifecycle_query(query, plan) and not any(has_lifecycle_provenance(item) for item in items):
        return {
            "label": "weak",
            "score": 0.0,
            "reasons": ["lifecycle_provenance_unavailable"],
            "must_say_not_found": True,
        }

    top = items[: int(config.get("top_items", 5))]
    primary_rate = sum(1 for item in top if item["is_primary"]) / len(top)
    page_rate = sum(1 for item in top if item["has_page"]) / len(top)
    constraints = plan.get("legal_constraints") or {}
    constraint_match_rate = sum(
        1 for item in top if row_matches_legal_constraints(item, constraints)
    ) / len(top) if constraints else 1.0
    article_rate = (
        sum(1 for item in top if row_matches_legal_constraints(item, constraints)) / len(top)
        if constraints.get("pasal")
        else sum(1 for item in top if item["has_article"]) / len(top)
    )
    matched_phrase_count = sum(len(item["matched_exact_phrases"]) for item in top)
    lexical_rate = sum(item["lexical_support"] for item in top) / len(top)
    issuer_hits = {item["issuer"] for item in top}
    expected_issuer_hits = [issuer for issuer in expected_issuers if issuer and issuer in issuer_hits]
    query_terms = set(tokenize_with_stopwords(query, load_stopwords()))
    evidence_text = " ".join(
        [
            item["citation"].get("document") or ""
            for item in top
        ]
        + [item.get("snippet") or "" for item in top]
    )
    covered_terms = query_terms & set(tokenize_with_stopwords(evidence_text, load_stopwords()))
    query_coverage = len(covered_terms) / max(1, len(query_terms))

    weights = config.get("weights") or {}
    score = 0.0
    score += float(weights.get("primary_rate", 0.25)) * primary_rate
    score += float(weights.get("page_rate", 0.20)) * page_rate
    score += float(weights.get("article_rate", 0.15)) * min(1.0, article_rate)
    score += float(weights.get("matched_phrase_rate", 0.15)) * min(1.0, matched_phrase_count / float(config.get("matched_phrase_normalizer", 2)))
    score += float(weights.get("lexical_rate", 0.15)) * lexical_rate
    score += float(weights.get("query_coverage", 0.10)) * query_coverage
    if expected_issuers:
        score += float(weights.get("expected_issuer_rate", 0.05)) * (len(expected_issuer_hits) / len([issuer for issuer in expected_issuers if issuer] or [None]))
    else:
        score += float(weights.get("expected_issuer_rate", 0.05))
    if (
        constraints.get("pasal")
        and constraints.get("regulation_number")
        and constraint_match_rate == 1.0
    ):
        score += float(config.get("exact_document_article_bonus", 0.08))

    reasons = [
        f"primary_rate={primary_rate:.2f}",
        f"page_rate={page_rate:.2f}",
        f"article_rate={article_rate:.2f}",
        f"matched_phrase_count={matched_phrase_count}",
        f"lexical_rate={lexical_rate:.2f}",
        f"query_coverage={query_coverage:.2f}",
    ]
    if constraints:
        reasons.append(f"legal_constraint_match_rate={constraint_match_rate:.2f}")
    if score >= float(config.get("strong_threshold", 0.78)):
        label = "strong"
    elif score >= float(config.get("partial_threshold", 0.55)):
        label = "partial"
    else:
        label = "weak"
    non_generic_entities = [entity for entity in plan.get("entities", []) if entity not in set(config.get("generic_entities") or [])]
    exact_legal_support = bool(constraints) and constraint_match_rate == 1.0
    if not ambiguous and not exact_legal_support and not plan.get("topics") and not non_generic_entities and matched_phrase_count == 0 and (
        query_coverage < float(config.get("generic_query_coverage_threshold", 0.75))
        or lexical_rate < float(config.get("generic_lexical_rate_threshold", 0.55))
    ):
        label = "weak"
        reasons.append("generic_entity_only_insufficient_support")
    if (
        not ambiguous
        and not exact_legal_support
        and matched_phrase_count == 0
        and query_coverage < float(config.get("low_coverage_query_threshold", 0.65))
        and lexical_rate < float(config.get("low_coverage_lexical_threshold", 0.50))
    ):
        label = "weak"
        reasons.append("low_coverage_without_exact_phrase_support")
    if constraints and constraint_match_rate < 1.0:
        label = "weak"
        reasons.append("requested_legal_constraint_not_satisfied")
    if label == "weak" and score >= float(config.get("partial_recovery_score_threshold", 0.70)) and (plan.get("topics") or non_generic_entities):
        label = "partial"
        reasons.append("topic_or_entity_supported_partial_evidence")
    score = min(1.0, score)
    return {
        "label": label,
        "score": round(score, 3),
        "reasons": reasons,
        "must_say_not_found": label == "weak",
    }

def build_evidence_pack(query: str, max_searches: int, limit: int, per_document_limit: int) -> dict[str, Any]:
    plan = build_query_plan(query, max_searches=max_searches)
    base_index = None if sqlite_index_is_current() else get_search_index(prefer_persisted=True)
    results = execute_query_plan(plan, limit, base_index=base_index)
    items = [evidence_item(query, row) for row in results]
    constraints = plan.get("legal_constraints") or {}
    ambiguous = bool(plan.get("ambiguity"))
    alignment_threshold = answer_alignment_threshold(query, plan)
    for item in items:
        item["legal_constraint_match"] = row_matches_legal_constraints(item, constraints)
        item["answer_alignment"] = answer_alignment(
            query,
            item,
            minimum_distinctive_ratio=alignment_threshold,
            allow_missing_value=ambiguous or query_requests_compound_answer(query),
            allow_missing_predicate=query_requests_compound_answer(query),
        ).to_dict()
    items.sort(key=lambda item: item["support_score"], reverse=True)

    retrieved_items = items
    items = [item for item in items if item["answer_alignment"]["accepted"]]

    grouped: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    effective_per_document_limit = (
        max(per_document_limit, limit)
        if query_requests_compound_answer(query)
        else per_document_limit
    )
    for item in items:
        citation = item["citation"]
        key = (item["issuer"], item["source_priority"], item["file_role"], citation["document"])
        if len(grouped[key]) < effective_per_document_limit:
            grouped[key].append(item)

    documents = []
    for (issuer, source_priority, file_role, document), doc_items in grouped.items():
        documents.append(
            {
                "document": document,
                "issuer": issuer,
                "source_priority": source_priority,
                "file_role": file_role,
                "top_score": max(item["support_score"] for item in doc_items),
                "evidence_count": len(doc_items),
                "citations": doc_items,
            }
        )
    documents.sort(key=lambda item: item["top_score"], reverse=True)

    expected_issuers = [issuer for issuer in plan["issuers"] if issuer]
    confidence = evidence_confidence(retrieved_items, expected_issuers, plan, query)
    pack = {
        "query": query,
        "plan": plan,
        "confidence": confidence,
        "documents": documents,
        "ungrouped_evidence": items,
        "answer_policy": {
            "primary_first": True,
            "required_best_effort_citations": ["document", "page", "pasal", "ayat"],
            "must_say_not_found_when_unsure": True,
        },
    }
    return apply_cross_regulator_confidence_gate(pack)

def format_evidence_pack(pack: dict[str, Any]) -> str:
    lines = [
        "# Evidence Pack",
        "",
        f"- Query: `{pack['query']}`",
        f"- Confidence: `{pack['confidence']['label']}` (`{pack['confidence']['score']}`)",
        f"- Must say not found: `{pack['confidence']['must_say_not_found']}`",
        f"- Intents: `{pack['plan']['intents']}`",
        f"- Issuers: `{pack['plan']['issuers']}`",
        f"- Topics: `{pack['plan']['topics']}`",
        f"- Entities: `{pack['plan']['entities']}`",
        "",
    ]
    if pack.get("topic_coverage"):
        coverage = pack["topic_coverage"]
        lines.extend(
            [
                "## Cross-Regulator Topic Coverage",
                "",
                f"- Applies: `{coverage.get('applies')}`",
                f"- Terms: `{coverage.get('terms')}`",
                f"- Missing direct issuers: `{coverage.get('missing_direct_issuers')}`",
                f"- Downgrade required: `{coverage.get('downgrade_required')}`",
                "",
            ]
        )
    lines.extend(["## Documents", ""])
    if not pack["documents"]:
        lines.append("No evidence found.")
        return "\n".join(lines) + "\n"

    for doc_index, doc in enumerate(pack["documents"], start=1):
        lines.extend(
            [
                f"### {doc_index}. {doc['document']}",
                "",
                f"- Issuer: `{doc['issuer']}`",
                f"- Source priority: `{doc.get('source_priority')}`",
                f"- Role: `{doc['file_role']}`",
                f"- Top score: `{doc['top_score']}`",
                f"- Evidence count: `{doc['evidence_count']}`",
                "",
            ]
        )
        for item_index, item in enumerate(doc["citations"], start=1):
            citation = item["citation"]
            lines.extend(
                [
                    f"{item_index}. {citation.get('text')}",
                    f"   - Citation quality: `{citation.get('quality')}`",
                    f"   - Section type: `{item.get('section_type')}`",
                    f"   - Planned query: `{item.get('planned_query')}`",
                    f"   - Reason: `{item.get('plan_reason')}`",
                    f"   - Matched phrases: `{item.get('matched_exact_phrases')}`",
                    f"   - Extraction flags: `{item.get('extraction_flags')}`",
                    f"   - Extraction quality multiplier: `{item.get('extraction_quality_multiplier')}`",
                    f"   - Exact phrase multiplier: `{item.get('exact_phrase_multiplier')}`",
                    f"   - Snippet: {item.get('snippet')}",
                    "",
                ]
            )
    return "\n".join(lines)

def cmd_evidence(args: argparse.Namespace) -> None:
    pack = build_evidence_pack(args.query, args.max_searches, args.limit, args.per_document_limit)
    output = format_evidence_pack(pack)
    print(output)
    if args.write_report:
        REPORTS_DIR.mkdir(exist_ok=True)
        stem = slugify(args.query)[:80] or "evidence"
        md_path = REPORTS_DIR / f"evidence_{stem}.md"
        json_path = REPORTS_DIR / f"evidence_{stem}.json"
        md_path.write_text(output, encoding="utf-8")
        json_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {md_path.relative_to(ROOT)}")
        print(f"Wrote {json_path.relative_to(ROOT)}")
