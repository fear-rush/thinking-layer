from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..common.io import iter_ndjson_file
from ..common.text import normalize_space
from ..config.heuristics import load_heuristic_config
from ..config.paths import REPORTS_DIR, ROOT, SOURCE_CORPUS_PATH


@dataclass(frozen=True)
class NoiseClassification:
    category: str
    matched_patterns: tuple[str, ...]
    answer_policy: str
    explicit_allowed: bool


def answer_noise_config() -> dict[str, Any]:
    return load_heuristic_config("answer_noise")


def query_allows_noise_category(query: str, category: str, config: dict[str, Any] | None = None) -> bool:
    config = config or answer_noise_config()
    query_l = query.lower()
    terms = ((config.get("explicit_request_terms") or {}).get(category) or [])
    return any(str(term).lower() in query_l for term in terms)


def classify_answer_noise(
    text: str,
    *,
    query: str = "",
    config: dict[str, Any] | None = None,
) -> NoiseClassification:
    config = config or answer_noise_config()
    normalized = normalize_space(text)
    categories = config.get("categories") or {}
    for category, category_config in categories.items():
        if category == "substantive":
            continue
        matched = []
        for pattern in category_config.get("patterns") or []:
            if re.search(str(pattern), normalized, flags=re.IGNORECASE):
                matched.append(str(pattern))
        if matched:
            return NoiseClassification(
                category=category,
                matched_patterns=tuple(matched),
                answer_policy=str(category_config.get("answer_policy") or "reject_by_default"),
                explicit_allowed=query_allows_noise_category(query, category, config),
            )
    substantive = categories.get("substantive") or {}
    return NoiseClassification(
        category="substantive",
        matched_patterns=(),
        answer_policy=str(substantive.get("answer_policy") or "allow"),
        explicit_allowed=True,
    )


def classify_evidence_item(
    item: dict[str, Any],
    *,
    query: str = "",
    config: dict[str, Any] | None = None,
) -> NoiseClassification:
    return classify_answer_noise(str(item.get("text") or item.get("snippet") or ""), query=query, config=config)


def should_use_claim_in_answer(
    item: dict[str, Any],
    *,
    query: str = "",
    config: dict[str, Any] | None = None,
) -> bool:
    classification = classify_evidence_item(item, query=query, config=config)
    if classification.category == "substantive":
        return True
    if classification.answer_policy == "allow":
        return True
    return classification.explicit_allowed


def answer_noise_rank_penalty(
    item: dict[str, Any],
    *,
    query: str = "",
    config: dict[str, Any] | None = None,
) -> float:
    config = config or answer_noise_config()
    classification = classify_evidence_item(item, query=query, config=config)
    if classification.category == "substantive" or classification.explicit_allowed:
        return 0.0
    ranking = config.get("ranking") or {}
    category_penalty = ranking.get("category_penalty") or {}
    return float(category_penalty.get(classification.category, ranking.get("default_reject_penalty", -100.0)))


def audit_answer_noise(
    source_path: Path = SOURCE_CORPUS_PATH,
    *,
    max_examples_per_category: int | None = None,
) -> dict[str, Any]:
    config = answer_noise_config()
    audit_config = config.get("audit") or {}
    max_examples = int(max_examples_per_category or audit_config.get("max_examples_per_category", 8))
    example_chars = int(audit_config.get("example_chars", 360))

    total = 0
    category_counts: Counter[str] = Counter()
    by_issuer: dict[str, Counter[str]] = defaultdict(Counter)
    by_role: dict[str, Counter[str]] = defaultdict(Counter)
    by_section_type: dict[str, Counter[str]] = defaultdict(Counter)
    matched_patterns: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in iter_ndjson_file(source_path):
        total += 1
        classification = classify_evidence_item(row, config=config)
        category = classification.category
        category_counts[category] += 1
        by_issuer[category][str(row.get("issuer") or "UNKNOWN")] += 1
        by_role[category][str(row.get("file_role") or "UNKNOWN")] += 1
        by_section_type[category][str(row.get("section_type") or "UNKNOWN")] += 1
        for pattern in classification.matched_patterns:
            matched_patterns[category][pattern] += 1
        if len(examples[category]) < max_examples:
            examples[category].append(
                {
                    "document": row.get("document_title"),
                    "issuer": row.get("issuer"),
                    "source": row.get("source"),
                    "file_role": row.get("file_role"),
                    "section_type": row.get("section_type"),
                    "citation": (row.get("citation") or {}).get("text"),
                    "matched_patterns": list(classification.matched_patterns),
                    "text": normalize_space(str(row.get("text") or ""))[:example_chars],
                }
            )

    def counter_dict(counter: Counter[str]) -> dict[str, int]:
        return dict(counter.most_common())

    categories = config.get("categories") or {}
    return {
        "source_path": str(source_path.relative_to(ROOT) if source_path.is_relative_to(ROOT) else source_path),
        "total_blocks": total,
        "categories": {
            category: {
                "description": (categories.get(category) or {}).get("description"),
                "answer_policy": (categories.get(category) or {}).get("answer_policy"),
                "count": category_counts.get(category, 0),
                "rate": round(category_counts.get(category, 0) / max(1, total), 5),
                "by_issuer": counter_dict(by_issuer[category]),
                "by_role": counter_dict(by_role[category]),
                "by_section_type": counter_dict(by_section_type[category]),
                "matched_patterns": counter_dict(matched_patterns[category]),
                "examples": examples.get(category, []),
            }
            for category in sorted(set(categories) | set(category_counts))
        },
        "boilerplate_blocks": total - category_counts.get("substantive", 0),
        "boilerplate_rate": round((total - category_counts.get("substantive", 0)) / max(1, total), 5),
    }


def write_answer_noise_audit(report: dict[str, Any], md_path: Path, json_path: Path) -> None:
    categories = report.get("categories") or {}
    lines = [
        "# Answer Noise Audit",
        "",
        "This report classifies legal boilerplate/noise patterns in `processed/source_corpus.ndjson` before changing answer behavior.",
        "",
        f"- Source: `{report['source_path']}`",
        f"- Total blocks: `{report['total_blocks']}`",
        f"- Boilerplate/noise blocks: `{report['boilerplate_blocks']}`",
        f"- Boilerplate/noise rate: `{report['boilerplate_rate']}`",
        "",
        "## Category Summary",
        "",
        "| Category | Policy | Count | Rate | Top section types |",
        "|---|---:|---:|---:|---|",
    ]
    for category, payload in sorted(categories.items(), key=lambda row: row[1].get("count", 0), reverse=True):
        section_types = ", ".join(f"{key}: {value}" for key, value in list((payload.get("by_section_type") or {}).items())[:4])
        lines.append(
            f"| `{category}` | `{payload.get('answer_policy')}` | `{payload.get('count')}` | `{payload.get('rate')}` | {section_types or '-'} |"
        )

    for category, payload in sorted(categories.items(), key=lambda row: row[1].get("count", 0), reverse=True):
        lines.extend(
            [
                "",
                f"## `{category}`",
                "",
                f"- Description: {payload.get('description') or '-'}",
                f"- Answer policy: `{payload.get('answer_policy')}`",
                f"- Count: `{payload.get('count')}`",
                f"- Rate: `{payload.get('rate')}`",
                f"- By issuer: `{payload.get('by_issuer')}`",
                f"- By role: `{payload.get('by_role')}`",
                f"- By section type: `{payload.get('by_section_type')}`",
                f"- Matched patterns: `{payload.get('matched_patterns')}`",
                "",
                "### Examples",
                "",
            ]
        )
        examples = payload.get("examples") or []
        if not examples:
            lines.append("No examples.")
            continue
        for example in examples:
            lines.extend(
                [
                    f"- `{example.get('issuer')}` `{example.get('file_role')}` `{example.get('section_type')}` - {example.get('document')}",
                    f"  - Citation: `{example.get('citation')}`",
                    f"  - Patterns: `{example.get('matched_patterns')}`",
                    f"  - Text: {example.get('text')}",
                    "",
                ]
            )

    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_answer_noise_audit(args: argparse.Namespace) -> None:
    source_path = Path(args.source_corpus) if args.source_corpus else SOURCE_CORPUS_PATH
    if not source_path.exists():
        raise SystemExit(f"Missing source corpus: {source_path}")
    REPORTS_DIR.mkdir(exist_ok=True)
    report = audit_answer_noise(source_path, max_examples_per_category=args.max_examples)
    md_path = REPORTS_DIR / "answer_noise_audit.md"
    json_path = REPORTS_DIR / "answer_noise_audit.json"
    write_answer_noise_audit(report, md_path, json_path)
    print(f"Wrote {md_path.relative_to(ROOT)}")
    print(f"Wrote {json_path.relative_to(ROOT)}")
    print(
        f"Classified {report['total_blocks']} blocks; "
        f"boilerplate/noise {report['boilerplate_blocks']} ({report['boilerplate_rate']})."
    )
