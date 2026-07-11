from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from ..config.paths import GOLD_QUESTIONS_PATH, REPORTS_DIR, ROOT
from ..indexing.semantic import _encode_documents, _encode_query, _load_model, semantic_config, semantic_text
from ..indexing.lexical import load_search_blocks
from ..indexing.sqlite import sqlite_index_exists, sqlite_search
from .evidence import load_gold_questions, title_matches_expected


def result_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("file_id"),
        row.get("page_start"),
        row.get("pasal"),
        row.get("ayat"),
        (row.get("text") or "")[:160],
    )


def dense_results(
    query: str,
    model: Any,
    model_name: str,
    blocks: list[dict[str, Any]],
    embeddings: np.ndarray,
    limit: int,
    normalize: bool,
) -> list[dict[str, Any]]:
    query_embedding = _encode_query(model, query, normalize, model_name=model_name)
    scores = embeddings @ query_embedding
    result_count = min(limit, len(blocks))
    positions = np.argpartition(-scores, result_count - 1)[:result_count]
    positions = positions[np.argsort(-scores[positions])]
    results = []
    for position in positions:
        row = dict(blocks[int(position)])
        row["_score"] = float(scores[int(position)])
        row["_semantic_score"] = row["_score"]
        row["_retriever"] = "dense"
        results.append(row)
    return results


def rrf_results(
    ranked_lists: list[list[dict[str, Any]]],
    limit: int,
    k: int = 60,
) -> list[dict[str, Any]]:
    fused: dict[tuple[Any, ...], dict[str, Any]] = {}
    scores: defaultdict[tuple[Any, ...], float] = defaultdict(float)
    for ranked in ranked_lists:
        for rank, row in enumerate(ranked, start=1):
            key = result_key(row)
            scores[key] += 1.0 / (k + rank)
            if key not in fused:
                fused[key] = dict(row)
    ordered = sorted(scores, key=scores.get, reverse=True)[:limit]
    results = []
    for key in ordered:
        row = fused[key]
        row["_score"] = scores[key]
        row["_rrf_score"] = scores[key]
        row["_retriever"] = "rrf"
        results.append(row)
    return results


def metric_row(spec: dict[str, Any], results: list[dict[str, Any]], cutoffs: tuple[int, ...]) -> dict[str, Any]:
    expected_documents = spec.get("expected_documents") or []
    required_issuers = spec.get("required_issuers") or []
    first_relevant_rank = None
    expected_hits_by_cutoff: dict[str, int] = {}
    for cutoff in cutoffs:
        top = results[:cutoff]
        matched = {
            expected
            for expected in expected_documents
            if any(title_matches_expected(row.get("document_title") or "", expected) for row in top)
        }
        expected_hits_by_cutoff[str(cutoff)] = len(matched)
        if first_relevant_rank is None and matched:
            first_relevant_rank = cutoff
    reciprocal_rank = 0.0
    for rank, row in enumerate(results, start=1):
        if any(title_matches_expected(row.get("document_title") or "", expected) for expected in expected_documents):
            reciprocal_rank = 1.0 / rank
            first_relevant_rank = rank
            break
    top_10 = results[:10]
    issuer_hits = sorted({issuer for issuer in required_issuers if any(row.get("issuer") == issuer for row in top_10)})
    return {
        "id": spec.get("id"),
        "query": spec.get("query"),
        "expected_behavior": spec.get("expected_behavior"),
        "expected_documents": expected_documents,
        "required_issuers": required_issuers,
        "document_hits": expected_hits_by_cutoff,
        "first_relevant_rank": first_relevant_rank,
        "reciprocal_rank": round(reciprocal_rank, 4),
        "issuer_hits": issuer_hits,
        "issuer_coverage": round(len(issuer_hits) / max(1, len(required_issuers)), 4),
        "top_titles": [row.get("document_title") for row in results[:5]],
    }


def summarize(rows: list[dict[str, Any]], cutoffs: tuple[int, ...]) -> dict[str, Any]:
    count = max(1, len(rows))
    mrr = sum(row["reciprocal_rank"] for row in rows) / count
    issuer_coverage = sum(row["issuer_coverage"] for row in rows) / count
    recall = {}
    for cutoff in cutoffs:
        values = []
        for row in rows:
            expected_count = len(row["expected_documents"])
            if not expected_count:
                continue
            values.append(min(1.0, row["document_hits"][str(cutoff)] / expected_count))
        recall[str(cutoff)] = round(sum(values) / max(1, len(values)), 4)
    return {
        "queries": len(rows),
        "mrr": round(mrr, 4),
        "issuer_coverage_at_10": round(issuer_coverage, 4),
        "document_recall": recall,
        "not_found_queries": sum(1 for row in rows if row["expected_behavior"] == "not_found"),
    }


def benchmark_model(
    model_name: str,
    specs: list[dict[str, Any]],
    blocks: list[dict[str, Any]],
    lexical_by_query: dict[str, list[dict[str, Any]]],
    limit: int,
    batch_size: int,
    normalize: bool,
    cutoffs: tuple[int, ...],
    progress: bool,
) -> dict[str, Any]:
    model = _load_model(model_name)
    max_text_chars = int(semantic_config().get("max_text_chars", 6000))
    texts = [semantic_text(block, max_text_chars) for block in blocks]
    embeddings = _encode_documents(model, texts, batch_size, normalize, model_name=model_name)
    dense_by_query: dict[str, list[dict[str, Any]]] = {}
    methods: dict[str, list[dict[str, Any]]] = {"dense": [], "rrf": []}
    for index, spec in enumerate(specs, start=1):
        query = spec["query"]
        if progress:
            print(f"{model_name}: query {index}/{len(specs)}", flush=True)
        dense = dense_results(query, model, model_name, blocks, embeddings, limit, normalize)
        lexical = lexical_by_query[query]
        dense_by_query[query] = dense
        methods["dense"].append(metric_row(spec, dense, cutoffs))
        methods["rrf"].append(metric_row(spec, rrf_results([lexical, dense], limit), cutoffs))
    return {
        "model": model_name,
        "block_count": len(blocks),
        "model_settings": semantic_config().get("models", {}).get(model_name, {}),
        "embedding_dimension": int(embeddings.shape[1]),
        "methods": {
            "dense": {"summary": summarize(methods["dense"], cutoffs), "queries": methods["dense"]},
            "rrf": {"summary": summarize(methods["rrf"], cutoffs), "queries": methods["rrf"]},
        },
    }


def write_report(report: dict[str, Any], path) -> None:
    lines = [
        "# Semantic Retrieval Benchmark",
        "",
        "This is a retrieval-only benchmark. It compares direct BM25, dense retrieval, and BM25+dense Reciprocal Rank Fusion on the development gold questions. It does not change production retrieval or claim answer/evidence quality improvements.",
        "",
        f"- Corpus blocks: `{report['block_count']}`",
        f"- Questions: `{report['question_count']}`",
        f"- Dense candidate depth: `{report['candidate_limit']}`",
        f"- RRF constant: `{report['rrf_k']}`",
        "- Cutoffs: `5`, `10`, `20`",
        "",
        "## BM25 Baseline",
        "",
        f"- MRR: `{report['bm25']['summary']['mrr']}`",
        f"- Document recall: `{report['bm25']['summary']['document_recall']}`",
        f"- Issuer coverage at 10: `{report['bm25']['summary']['issuer_coverage_at_10']}`",
        "",
        "## Dense And RRF",
        "",
    ]
    for model in report["models"]:
        lines.extend(
            [
                f"### `{model['model']}`",
                "",
            ]
        )
        if model.get("status") == "error":
            lines.extend(
                [
                    "- Status: `error`",
                    f"- Error type: `{model.get('error_type', 'Exception')}`",
                    f"- Error: `{model.get('error', 'unknown error')}`",
                    "",
                ]
            )
            continue
        lines.extend(
            [
                f"- Dimensions: `{model['embedding_dimension']}`",
                f"- Dense MRR: `{model['methods']['dense']['summary']['mrr']}`",
                f"- Dense document recall: `{model['methods']['dense']['summary']['document_recall']}`",
                f"- Dense issuer coverage at 10: `{model['methods']['dense']['summary']['issuer_coverage_at_10']}`",
                f"- RRF MRR: `{model['methods']['rrf']['summary']['mrr']}`",
                f"- RRF document recall: `{model['methods']['rrf']['summary']['document_recall']}`",
                f"- RRF issuer coverage at 10: `{model['methods']['rrf']['summary']['issuer_coverage_at_10']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation Guardrails",
            "",
            "- Not-found questions are included in the query rows but are excluded from document-recall averaging because retrieval alone has no calibrated refusal threshold.",
            "- The bounded corpus slice and development gold set are suitable for implementation comparison, not final model selection.",
            "- A model must improve recall without increasing irrelevant or boilerplate evidence before it can replace or augment BM25 in the evidence and answer evaluations.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_benchmark_retrieval(args: argparse.Namespace) -> None:
    if not sqlite_index_exists():
        raise SystemExit("Missing SQLite lexical index. Run `build-index` before benchmarking.")
    config = semantic_config()
    model_names = [name.strip() for name in (args.models or ",".join(config.get("model_candidates") or [])).split(",") if name.strip()]
    if not model_names:
        raise SystemExit("No semantic models configured.")
    specs = load_gold_questions(Path(args.gold_file) if args.gold_file else GOLD_QUESTIONS_PATH)
    if args.question_limit:
        specs = specs[: args.question_limit]
    blocks = load_search_blocks(None, None, None, include_secondary=True)
    if args.corpus_limit:
        blocks = blocks[: args.corpus_limit]
    if not blocks:
        raise SystemExit("No source-corpus blocks available.")
    lexical_by_query = {spec["query"]: sqlite_search(spec["query"], args.candidate_limit, include_secondary=True) for spec in specs}
    cutoffs = (5, 10, 20)
    baseline_rows = [metric_row(spec, lexical_by_query[spec["query"]], cutoffs) for spec in specs]
    report = {
        "question_count": len(specs),
        "block_count": len(blocks),
        "candidate_limit": args.candidate_limit,
        "rrf_k": 60,
        "bm25": {"summary": summarize(baseline_rows, cutoffs), "queries": baseline_rows},
        "models": [],
    }
    for model_name in model_names:
        try:
            report["models"].append(
                benchmark_model(
                    model_name,
                    specs,
                    blocks,
                    lexical_by_query,
                    args.candidate_limit,
                    args.batch_size,
                    args.normalize_embeddings,
                    cutoffs,
                    args.progress,
                )
            )
        except Exception as exc:
            failure = {
                "model": model_name,
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "model_settings": semantic_config().get("models", {}).get(model_name, {}),
            }
            report["models"].append(failure)
            print(f"{model_name}: benchmark error ({type(exc).__name__}): {exc}", flush=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    prefix = args.report_prefix or "semantic_retrieval_benchmark"
    json_path = REPORTS_DIR / f"{prefix}.json"
    md_path = REPORTS_DIR / f"{prefix}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(report, md_path)
    print(f"Wrote {md_path.relative_to(ROOT)}")
    print(f"Wrote {json_path.relative_to(ROOT)}")


if __name__ == "__main__":
    raise SystemExit("Use `thinking_layer.cli benchmark-retrieval`.")
