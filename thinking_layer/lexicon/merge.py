from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..common.io import read_json
from ..config.paths import GENERATED_LEXICON_PATH, QUERY_LEXICON_PATH, REVIEWED_LEXICON_PATH, ROOT

def merge_generated_lexicon(base: dict[str, Any], reviewed: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(base, ensure_ascii=False))
    for section in ("entities", "topics"):
        existing_names = {item.get("name") for item in merged.get(section, [])}
        existing_patterns = {
            pattern.lower()
            for item in merged.get(section, [])
            for pattern in item.get("patterns", [])
            if isinstance(pattern, str)
        }
        for item in reviewed.get(section, []):
            if item.get("approved") is not True:
                continue
            patterns = [pattern for pattern in item.get("patterns", []) if isinstance(pattern, str)]
            if item.get("name") in existing_names or any(pattern.lower() in existing_patterns for pattern in patterns):
                continue
            clean_item = {key: value for key, value in item.items() if key not in {"approved", "review_notes"}}
            merged.setdefault(section, []).append(clean_item)
            existing_names.add(clean_item.get("name"))
            existing_patterns.update(pattern.lower() for pattern in patterns)
    return merged

def cmd_merge_lexicon(args: argparse.Namespace) -> None:
    if not REVIEWED_LEXICON_PATH.exists():
        raise SystemExit(f"Missing {REVIEWED_LEXICON_PATH.relative_to(ROOT)}. Review {GENERATED_LEXICON_PATH.relative_to(ROOT)} first.")
    base = read_json(QUERY_LEXICON_PATH)
    reviewed = read_json(REVIEWED_LEXICON_PATH)
    merged = merge_generated_lexicon(base, reviewed)
    output_path = Path(args.output)
    output_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path.relative_to(ROOT) if output_path.is_relative_to(ROOT) else output_path}")
