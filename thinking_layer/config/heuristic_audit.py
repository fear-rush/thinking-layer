from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .paths import CONFIG_DIR, REPORTS_DIR, ROOT


CONFIG_CATEGORIES = {
    "answer_ranking": "manual_domain_policy",
    "answer_noise": "corpus_noise_filter",
    "cross_regulator_confidence": "manual_domain_policy",
    "extraction_spot_check": "evaluation_rubric",
    "retrieval_ranking": "manual_domain_policy",
    "evidence_confidence": "evaluation_rubric",
    "evaluation_rubrics": "evaluation_rubric",
    "extraction_heuristics": "parser_heuristic",
    "lexicon_extraction": "manual_domain_seed",
    "semantic_retrieval": "standard_ir",
}

SECTION_CATEGORIES = {
    "bm25": "standard_ir",
    "role_boost": "manual_domain_policy",
    "sector_alignment": "manual_domain_seed",
    "query_planning": "manual_domain_seed",
    "title_phrase_patterns": "manual_domain_seed",
    "topic_hints": "manual_domain_seed",
    "entity_hints": "manual_domain_seed",
    "generic_terms": "corpus_noise_filter",
    "generic_fragments": "corpus_noise_filter",
    "noisy_answer_patterns": "corpus_noise_filter",
    "explicit_request_terms": "manual_domain_policy",
    "categories": "corpus_noise_filter",
    "patterns": "corpus_noise_filter",
    "claim_text": "corpus_noise_filter",
    "usable_claim": "corpus_noise_filter",
}


def load_config(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def category_for(config_name: str, key_path: list[str]) -> str:
    for key in reversed(key_path):
        if key in SECTION_CATEGORIES:
            return SECTION_CATEGORIES[key]
    return CONFIG_CATEGORIES.get(config_name, "manual_domain_policy")


def iter_leaf_values(value: Any, prefix: list[str] | None = None):
    prefix = prefix or []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "metadata":
                continue
            yield from iter_leaf_values(child, [*prefix, key])
    elif isinstance(value, list):
        yield prefix, value
    else:
        yield prefix, value


def format_value(value: Any) -> str:
    if isinstance(value, list):
        if len(value) > 12:
            return f"`{json.dumps(value[:12], ensure_ascii=False)}` ... ({len(value)} items)"
        return f"`{json.dumps(value, ensure_ascii=False)}`"
    return f"`{value}`"


def write_heuristics_audit(path: Path) -> None:
    lines = [
        "# Heuristics Audit",
        "",
        "This report lists behavior-affecting heuristic values loaded from `resources/config/`.",
        "The current pass is behavior-preserving: values were externalized, not tuned.",
        "",
    ]
    for config_path in sorted(CONFIG_DIR.glob("*.json")):
        config_name = config_path.stem
        config = load_config(config_path)
        metadata = config.get("metadata") or {}
        lines.extend(
            [
                f"## {config_path.relative_to(ROOT)}",
                "",
                f"- Description: {metadata.get('description', '-')}",
                f"- Calibrated: `{metadata.get('calibrated', False)}`",
                "",
            ]
        )
        for key_path, value in iter_leaf_values(config):
            key = ".".join([config_name, *key_path])
            lines.extend(
                [
                    f"### `{key}`",
                    "",
                    f"- Value: {format_value(value)}",
                    f"- Category: `{category_for(config_name, key_path)}`",
                    "- Affects runtime: `yes`",
                    "- Calibration status: `not calibrated`",
                    "",
                ]
            )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def cmd_heuristics_audit(_args: argparse.Namespace) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / "heuristics_audit.md"
    write_heuristics_audit(path)
    print(f"Wrote {path.relative_to(ROOT)}")
