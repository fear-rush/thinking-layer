from __future__ import annotations

import argparse
import json
import sqlite3
import time
import zlib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from math import floor
from pathlib import Path
from typing import Any

from ..answer.composer import build_answer
from ..config.paths import SEARCH_INDEX_DB


DEFAULT_GOLDEN_PATH = Path(__file__).resolve().parents[2] / "resources" / "golden_questions.v2.json"


def load_golden_suite(path: Path = DEFAULT_GOLDEN_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        raise ValueError("golden suite must be an object with a cases array")
    return payload


def validate_golden_suite(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    cases = payload.get("cases") or []
    ids = [case.get("id") for case in cases]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        errors.append("case ids must be present and unique")
    tiers = (payload.get("metadata") or {}).get("tiers") or {}
    if tiers.get("full") != "all":
        errors.append("metadata.tiers.full must be 'all'")
    smoke_ids = tiers.get("smoke") or []
    if not smoke_ids or len(smoke_ids) != len(set(smoke_ids)):
        errors.append("metadata.tiers.smoke must contain unique case ids")
    unknown_smoke_ids = sorted(set(smoke_ids) - set(ids))
    if unknown_smoke_ids:
        errors.append(f"metadata.tiers.smoke contains unknown ids: {unknown_smoke_ids}")
    for case in cases:
        prefix = str(case.get("id") or "<missing>")
        expected = case.get("expected") or {}
        statuses = expected.get("statuses") or []
        if not case.get("query"):
            errors.append(f"{prefix}: query is required")
        if not case.get("category"):
            errors.append(f"{prefix}: category is required")
        if not statuses:
            errors.append(f"{prefix}: expected.statuses is required")
        citations_spec = expected.get("citations") or {}
        targets = citations_spec.get("targets") or []
        allowed_targets = citations_spec.get("allowed_targets") or []
        must_be_empty = bool(citations_spec.get("must_be_empty"))
        if (statuses == ["not_found"] or must_be_empty) and targets:
            errors.append(f"{prefix}: not_found cases cannot have citation targets")
        if (statuses == ["not_found"] or must_be_empty) and allowed_targets:
            errors.append(f"{prefix}: citation-free cases cannot have allowed citation targets")
        if statuses != ["not_found"] and not must_be_empty and not targets:
            errors.append(f"{prefix}: answer cases require exact citation targets")
        if not (expected.get("answer") or {}).get("required_term_groups"):
            errors.append(f"{prefix}: expected.answer.required_term_groups is required")
        for target in [*targets, *allowed_targets]:
            variants = target.get("variants") or []
            if not target.get("name") or not variants:
                errors.append(f"{prefix}: every target needs a name and variants")
            for variant in variants:
                required = ("issuer", "file_id", "page_start", "page_end", "legal_path")
                missing = [key for key in required if variant.get(key) in (None, "", {})]
                if missing:
                    errors.append(f"{prefix}/{target.get('name')}: missing {missing}")
    return errors


def _split_filters(values: list[str] | None) -> list[str]:
    return [item.strip() for value in values or [] for item in value.split(",") if item.strip()]


def select_cases(
    payload: dict[str, Any],
    tier: str = "full",
    case_ids: list[str] | None = None,
    categories: list[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    cases = list(payload["cases"])
    cases_by_id = {case["id"]: case for case in cases}
    tiers = payload["metadata"]["tiers"]
    if tier not in tiers:
        raise ValueError(f"unknown tier: {tier}")
    tier_ids = list(cases_by_id) if tiers[tier] == "all" else list(tiers[tier])
    selected_ids = set(tier_ids)

    requested_ids = _split_filters(case_ids)
    unknown_ids = sorted(set(requested_ids) - set(cases_by_id))
    if unknown_ids:
        raise ValueError(f"unknown case ids: {unknown_ids}")
    if requested_ids:
        selected_ids &= set(requested_ids)

    requested_categories = _split_filters(categories)
    known_categories = {case["category"] for case in cases}
    unknown_categories = sorted(set(requested_categories) - known_categories)
    if unknown_categories:
        raise ValueError(f"unknown categories: {unknown_categories}")
    if requested_categories:
        selected_ids &= {case["id"] for case in cases if case["category"] in requested_categories}

    selected = [case for case in cases if case["id"] in selected_ids]
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive")
        selected = selected[:limit]
    if not selected:
        raise ValueError("filters selected no golden cases")
    return selected


def _text(value: Any) -> str:
    return str(value or "").strip().casefold()


def _answer_display_text(answer: dict[str, Any]) -> str:
    values = [answer.get("answer"), answer.get("summary")]
    values.extend(finding.get("text") for finding in answer.get("findings") or [])
    values.extend(answer.get("limitations") or [])
    return "\n".join(str(value or "") for value in values)


def _citation_legal_path(citation: dict[str, Any]) -> dict[str, Any]:
    path = dict(citation.get("legal_path") or {})
    for key in ("bab", "bagian", "paragraf", "pasal", "ayat", "huruf", "angka"):
        if citation.get(key) and not path.get(key):
            path[key] = citation[key]
    return path


def citation_matches_variant(citation: dict[str, Any], variant: dict[str, Any]) -> bool:
    if _text(citation.get("issuer")) != _text(variant.get("issuer")):
        return False
    if _text(citation.get("file_id")) != _text(variant.get("file_id")):
        return False
    citation_start = int(citation.get("page_start") or citation.get("page") or 0)
    citation_end = int(citation.get("page_end") or citation_start)
    target_start = int(variant["page_start"])
    target_end = int(variant["page_end"])
    if citation_end < target_start or citation_start > target_end:
        return False
    actual_path = _citation_legal_path(citation)
    if any(_text(actual_path.get(key)) != _text(value) for key, value in variant["legal_path"].items()):
        return False
    citation_text = "\n".join(
        str(citation.get(key) or "") for key in ("excerpt", "assembled_text", "text")
    ).casefold()
    return all(_text(term) in citation_text for term in variant.get("text_terms") or [])


def preflight_exact_targets(
    cases: list[dict[str, Any]], database_path: Path = SEARCH_INDEX_DB
) -> dict[str, Any]:
    if not database_path.exists():
        return {
            "passed": False,
            "checked_variants": 0,
            "matched_variants": 0,
            "failures": [{"reason": f"missing search index: {database_path}"}],
        }
    variants_by_file: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}
    for case in cases:
        citations_spec = case["expected"]["citations"]
        for target in [
            *(citations_spec.get("targets") or []),
            *(citations_spec.get("allowed_targets") or []),
        ]:
            for variant in target["variants"]:
                variants_by_file.setdefault(variant["file_id"], []).append((case["id"], target["name"], variant))

    failures: list[dict[str, Any]] = []
    matched = 0
    connection = sqlite3.connect(database_path)
    try:
        for file_id, variant_specs in variants_by_file.items():
            rows = []
            for (raw,) in connection.execute("SELECT block_json FROM docs WHERE file_id = ?", (file_id,)):
                block = json.loads(zlib.decompress(raw))
                block["excerpt"] = block.get("display_text")
                rows.append(block)
            for case_id, target_name, variant in variant_specs:
                if any(citation_matches_variant(row, variant) for row in rows):
                    matched += 1
                else:
                    failures.append(
                        {
                            "case_id": case_id,
                            "target": target_name,
                            "file_id": file_id,
                            "page_start": variant["page_start"],
                            "page_end": variant["page_end"],
                            "legal_path": variant["legal_path"],
                            "reason": "exact target is absent from the current v2 index",
                        }
                    )
    except (sqlite3.DatabaseError, json.JSONDecodeError, zlib.error) as error:
        failures.append({"reason": f"search index preflight failed: {error}"})
    finally:
        connection.close()
    checked = sum(len(values) for values in variants_by_file.values())
    return {
        "passed": not failures,
        "checked_variants": checked,
        "matched_variants": matched,
        "failures": failures,
    }


def _target_hits(
    targets: list[dict[str, Any]], citations: list[dict[str, Any]]
) -> tuple[list[str], list[int]]:
    hit_names: list[str] = []
    matched_citation_indexes: list[int] = []
    for target in targets:
        hit = False
        for index, citation in enumerate(citations):
            if any(citation_matches_variant(citation, variant) for variant in target["variants"]):
                hit = True
                matched_citation_indexes.append(index)
        if hit:
            hit_names.append(target["name"])
    return hit_names, sorted(set(matched_citation_indexes))


def _has_v2_provenance(citation: dict[str, Any]) -> bool:
    page_start = int(citation.get("page_start") or citation.get("page") or 0)
    page_end = int(citation.get("page_end") or page_start)
    return bool(
        citation.get("chunk_schema_version") == 2
        and citation.get("file_id")
        and citation.get("block_id")
        and citation.get("source_block_ids")
        and citation.get("anchors")
        and citation.get("legal_path")
        and page_start > 0
        and page_end >= page_start
    )


def evaluate_golden_answer(spec: dict[str, Any], answer: dict[str, Any], gates: dict[str, Any]) -> dict[str, Any]:
    expected = spec["expected"]
    citations_spec = expected.get("citations") or {}
    citations = list(answer.get("citations") or [])
    findings = list(answer.get("findings") or [])
    statuses = expected["statuses"]
    is_not_found = statuses == ["not_found"]
    must_be_empty = bool(citations_spec.get("must_be_empty"))
    answer_text = _answer_display_text(answer).casefold()

    status_ok = answer.get("status") in statuses
    required_groups = expected.get("answer", {}).get("required_term_groups") or []
    answer_terms_ok = all(any(_text(term) in answer_text for term in group) for group in required_groups)
    forbidden_terms = expected.get("answer", {}).get("forbidden_terms") or []
    forbidden_terms_ok = not any(_text(term) in answer_text for term in forbidden_terms)
    uncertainty_terms = expected.get("answer", {}).get("uncertainty_terms") or []
    uncertainty_ok = not uncertainty_terms or any(_text(term) in answer_text for term in uncertainty_terms)

    required_issuers = expected.get("required_issuers") or []
    issuer_hits = sorted({citation.get("issuer") for citation in citations if citation.get("issuer") in required_issuers})
    issuers_ok = len(issuer_hits) == len(required_issuers)

    targets = citations_spec.get("targets") or []
    target_hits, matched_indexes = _target_hits(targets, citations)
    allowed_target_hits, allowed_indexes = _target_hits(
        citations_spec.get("allowed_targets") or [], citations
    )
    matched_indexes = sorted(set(matched_indexes) | set(allowed_indexes))
    target_mode = citations_spec.get("target_mode", "all")
    if is_not_found or must_be_empty:
        target_recall = 1.0 if not citations and not findings else 0.0
        target_ok = bool(target_recall)
        citation_precision = 1.0 if not citations else 0.0
        provenance_ok = not citations
    else:
        target_recall = len(target_hits) / max(1, len(targets))
        target_ok = bool(target_hits) if target_mode == "any" else len(target_hits) == len(targets)
        citation_precision = len(matched_indexes) / max(1, len(citations))
        provenance_ok = bool(citations) and all(_has_v2_provenance(citation) for citation in citations)

    min_citations = int(citations_spec.get("min_citations", 0 if is_not_found or must_be_empty else 1))
    max_citations = int(citations_spec.get("max_citations", 0 if is_not_found or must_be_empty else 6))
    citation_count_ok = min_citations <= len(citations) <= max_citations
    precision_ok = citation_precision >= float(
        citations_spec.get("min_precision", gates.get("min_exact_citation_precision", 0.67))
    )

    checks = {
        "status": status_ok,
        "answer_terms": answer_terms_ok,
        "forbidden_terms": forbidden_terms_ok,
        "uncertainty": uncertainty_ok,
        "required_issuers": issuers_ok,
        "exact_targets": target_ok,
        "citation_count": citation_count_ok,
        "citation_precision": precision_ok,
        "v2_provenance": provenance_ok,
    }
    weights = gates.get("weights") or {
        "status": 0.15,
        "answer_terms": 0.15,
        "exact_targets": 0.30,
        "citation_precision": 0.15,
        "v2_provenance": 0.10,
        "required_issuers": 0.05,
        "citation_count": 0.05,
        "uncertainty": 0.03,
        "forbidden_terms": 0.02,
    }
    score = sum(float(weight) for name, weight in weights.items() if checks.get(name))
    hard_checks = gates.get("hard_checks") or list(checks)
    failures = [name for name in hard_checks if not checks.get(name)]
    accepted = score >= float(gates.get("accepted_score", 0.90)) and not failures
    return {
        "id": spec["id"],
        "category": spec["category"],
        "accepted": accepted,
        "score": round(score, 3),
        "status": answer.get("status"),
        "citation_count": len(citations),
        "target_recall": round(target_recall, 3),
        "citation_precision": round(citation_precision, 3),
        "target_hits": target_hits,
        "allowed_target_hits": allowed_target_hits,
        "required_issuers": required_issuers,
        "issuer_hits": issuer_hits,
        "checks": checks,
        "failure_reasons": failures,
    }


def _run_case(spec: dict[str, Any], gates: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    answer = build_answer(spec["query"], 8, 12, 3, 6, 2)
    evaluation = evaluate_golden_answer(spec, answer, gates)
    evaluation["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
    return {"spec": spec, "evaluation": evaluation}


def run_suite(
    payload: dict[str, Any],
    limit: int | None = None,
    jobs: int = 1,
    tier: str = "full",
    case_ids: list[str] | None = None,
    categories: list[str] | None = None,
) -> list[dict[str, Any]]:
    errors = validate_golden_suite(payload)
    if errors:
        raise ValueError("invalid golden suite: " + "; ".join(errors))
    cases = select_cases(payload, tier=tier, case_ids=case_ids, categories=categories, limit=limit)
    gates = payload["metadata"]["gates"]
    if jobs <= 1:
        rows = []
        for index, spec in enumerate(cases, start=1):
            print(f"[{index}/{len(cases)}] {spec['id']}", flush=True)
            rows.append(_run_case(spec, gates))
        return rows
    ordered: list[dict[str, Any] | None] = [None] * len(cases)
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        future_indexes = {executor.submit(_run_case, spec, gates): index for index, spec in enumerate(cases)}
        for completed, future in enumerate(as_completed(future_indexes), start=1):
            index = future_indexes[future]
            ordered[index] = future.result()
            print(f"[{completed}/{len(cases)}] {cases[index]['id']}", flush=True)
    return [row for row in ordered if row is not None]


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = floor(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = sum(row["evaluation"]["accepted"] for row in rows)
    hard_failures = Counter(
        failure
        for row in rows
        for failure in row["evaluation"].get("failure_reasons") or []
    )
    latencies = [float(row["evaluation"].get("latency_ms") or 0.0) for row in rows]
    by_category: dict[str, dict[str, int]] = {}
    for category, count in Counter(row["evaluation"]["category"] for row in rows).items():
        category_rows = [row for row in rows if row["evaluation"]["category"] == category]
        by_category[category] = {
            "accepted": sum(row["evaluation"]["accepted"] for row in category_rows),
            "total": count,
        }
    return {
        "accepted": accepted,
        "total": len(rows),
        "acceptance_rate": round(accepted / max(1, len(rows)), 3),
        "average_score": round(sum(row["evaluation"]["score"] for row in rows) / max(1, len(rows)), 3),
        "hard_failure_counts": dict(sorted(hard_failures.items())),
        "latency_ms": {
            "p50": round(_percentile(latencies, 0.50), 3),
            "p95": round(_percentile(latencies, 0.95), 3),
            "max": round(max(latencies, default=0.0), 3),
            "total": round(sum(latencies), 3),
        },
        "by_category": by_category,
    }


def compare_summaries(current: dict[str, Any], prior: dict[str, Any]) -> dict[str, Any]:
    current_failures = current.get("hard_failure_counts") or {}
    prior_failures = prior.get("hard_failure_counts") or {}
    failure_names = sorted(set(current_failures) | set(prior_failures))
    current_latency = current.get("latency_ms") or {}
    prior_latency = prior.get("latency_ms") or {}
    return {
        "accepted_delta": int(current.get("accepted") or 0) - int(prior.get("accepted") or 0),
        "acceptance_rate_delta": round(
            float(current.get("acceptance_rate") or 0.0) - float(prior.get("acceptance_rate") or 0.0), 3
        ),
        "average_score_delta": round(
            float(current.get("average_score") or 0.0) - float(prior.get("average_score") or 0.0), 3
        ),
        "latency_ms_delta": {
            "p50": round(float(current_latency.get("p50") or 0.0) - float(prior_latency.get("p50") or 0.0), 3),
            "p95": round(float(current_latency.get("p95") or 0.0) - float(prior_latency.get("p95") or 0.0), 3),
            "max": round(float(current_latency.get("max") or 0.0) - float(prior_latency.get("max") or 0.0), 3),
        },
        "hard_failure_count_delta": {
            name: int(current_failures.get(name) or 0) - int(prior_failures.get(name) or 0)
            for name in failure_names
        },
        "comparable_case_count": current.get("total") == prior.get("total"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exact legal-target golden evaluation.")
    parser.add_argument("--gold-file", type=Path, default=DEFAULT_GOLDEN_PATH)
    parser.add_argument("--tier", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--case-id", action="append", help="Case id or comma-separated ids; repeatable.")
    parser.add_argument("--category", action="append", help="Category or comma-separated categories; repeatable.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--jobs", type=int, default=1, help="Concurrent read-only evaluations.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--compare-to", type=Path, help="Prior JSON report produced by this runner.")
    parser.add_argument("--preflight-only", action="store_true", help="Validate exact corpus targets without answering.")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip the default exact-target corpus check.")
    args = parser.parse_args()
    payload = load_golden_suite(args.gold_file)
    errors = validate_golden_suite(payload)
    if errors:
        raise SystemExit("invalid golden suite: " + "; ".join(errors))
    cases = select_cases(
        payload,
        tier=args.tier,
        case_ids=args.case_id,
        categories=args.category,
        limit=args.limit,
    )
    preflight = (
        {"passed": True, "checked_variants": 0, "matched_variants": 0, "failures": [], "skipped": True}
        if args.skip_preflight
        else preflight_exact_targets(cases)
    )
    if not preflight["passed"]:
        raise SystemExit(json.dumps(preflight, ensure_ascii=False, indent=2))

    report_metadata = {
        "suite": payload["metadata"]["suite"],
        "suite_version": payload["metadata"]["version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tier": args.tier,
        "selected_case_ids": [case["id"] for case in cases],
        "case_id_filters": _split_filters(args.case_id),
        "category_filters": _split_filters(args.category),
        "jobs": max(1, args.jobs),
    }
    if args.preflight_only:
        result = {"metadata": report_metadata, "preflight": preflight, "summary": None, "rows": []}
    else:
        started = time.perf_counter()
        rows = run_suite(
            payload,
            args.limit,
            jobs=max(1, args.jobs),
            tier=args.tier,
            case_ids=args.case_id,
            categories=args.category,
        )
        summary = summarize(rows)
        summary["wall_time_ms"] = round((time.perf_counter() - started) * 1000, 3)
        result = {"metadata": report_metadata, "preflight": preflight, "summary": summary, "rows": rows}
        if args.compare_to:
            prior = json.loads(args.compare_to.read_text(encoding="utf-8"))
            prior_summary = prior.get("summary") or {}
            result["comparison"] = compare_summaries(summary, prior_summary)
            result["comparison"]["same_case_ids"] = (
                report_metadata["selected_case_ids"] == (prior.get("metadata") or {}).get("selected_case_ids")
            )
    print(json.dumps({key: result[key] for key in result if key != "rows"}, ensure_ascii=False, indent=2))
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
