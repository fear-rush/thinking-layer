from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..common.io import iter_ndjson_file, read_ndjson_file
from ..config.heuristics import load_heuristic_config
from ..config.paths import (
    GENERATED_LEXICON_PATH,
    LEXICON_DIR,
    LEXICON_CANDIDATES_PATH,
    PROCESSED_DIR,
    QUERY_LEXICON_PATH,
    REPORTS_DIR,
    REVIEWED_LEXICON_PATH,
    ROOT,
)
from ..retrieval.query_tools import tokenize, unique_keep_order
from ..common.text import normalize_space, slugify

LEXICON_CONFIG = load_heuristic_config("lexicon_extraction")

def config_set(key: str) -> set[str]:
    return set(LEXICON_CONFIG.get(key) or [])

def config_section(key: str) -> dict[str, Any]:
    value = LEXICON_CONFIG.get(key) or {}
    if not isinstance(value, dict):
        raise SystemExit(f"resources/config/lexicon_extraction.json section `{key}` must be an object")
    return value

def lexicon_normalize_phrase(value: str) -> str:
    value = normalize_space(value)
    value = re.sub(r"^[#\-\d.)\s]+", "", value)
    value = re.sub(r"^(?:[IVXLCDM]+|[A-Z])\.\s+", "", value)
    value = re.sub(r"^(?:POJK|SEOJK|PBI|PADG|PADK|SEBI|UU|PP|PMK)\b[^-:–—]*[-:–—]\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:POJK|SEOJK|PBI|PADG|PADK|SEBI|UU|PP|PMK)\s+(?:tentang|perihal)\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(?:tentang|perihal)\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*\([^)]{1,80}\)\s*$", "", value)
    value = normalize_space(value.strip(" .,:;-/–—"))
    return value

def lexicon_key(value: str) -> str:
    return normalize_space(value.lower())

def lexicon_candidate_type(phrase: str, source_hint: str | None = None) -> str:
    lowered = phrase.lower()
    if source_hint == "alias":
        return "alias"
    if any(hint in lowered for hint in config_set("entity_hints")):
        return "entity"
    if any(hint in lowered for hint in config_set("topic_hints")):
        return "topic"
    if re.fullmatch(str(config_section("validation").get("alias_regex", r"[A-Z0-9-]{2,12}")), phrase.strip()):
        return "alias"
    return "topic"

def lexicon_phrase_valid(phrase: str) -> bool:
    validation = config_section("validation")
    generic_terms = config_set("generic_terms")
    lowered = lexicon_key(phrase)
    if not lowered or lowered in generic_terms:
        return False
    if lowered in config_set("invalid_exact_terms"):
        return False
    if any(fragment in lowered for fragment in config_set("generic_fragments")):
        return False
    if any(marker in phrase for marker in LEXICON_CONFIG.get("invalid_markers") or []):
        return False
    if len(lowered) < int(validation.get("min_phrase_chars", 3)) or len(lowered) > int(validation.get("max_phrase_chars", 160)):
        return False
    if re.fullmatch(str(validation.get("numeric_only_regex", r"[\d./\-\s]+")), lowered):
        return False
    tokens = tokenize(lowered)
    if len(tokens) > int(validation.get("max_tokens", 10)):
        return False
    if len(tokens) == 0:
        return False
    if (
        len(tokens) == 1
        and len(tokens[0]) < int(validation.get("single_token_min_chars", 4))
        and not re.fullmatch(str(validation.get("single_token_alias_regex", r"[a-z]{2,6}")), tokens[0])
    ):
        return False
    generic_hits = sum(1 for token in tokens if token in generic_terms)
    return generic_hits < max(1, len(tokens) // 2)

def add_lexicon_candidate(
    candidates: dict[tuple[str, str], dict[str, Any]],
    phrase: str,
    candidate_type: str,
    source: str,
    weight: float,
    row: dict[str, Any] | None = None,
    alias_of: str | None = None,
) -> None:
    phrase = lexicon_normalize_phrase(phrase)
    if not lexicon_phrase_valid(phrase):
        return
    candidate_type = candidate_type or lexicon_candidate_type(phrase)
    key = (candidate_type, lexicon_key(phrase))
    item = candidates.setdefault(
        key,
        {
            "phrase": phrase,
            "type": candidate_type,
            "score": 0.0,
            "support_count": 0,
            "sources": Counter(),
            "issuers": Counter(),
            "file_roles": Counter(),
            "aliases": set(),
            "alias_of": set(),
            "examples": [],
        },
    )
    item["score"] += weight
    item["support_count"] += 1
    item["sources"][source] += 1
    if row:
        if row.get("issuer"):
            item["issuers"][row["issuer"]] += 1
        if row.get("file_role"):
            item["file_roles"][row["file_role"]] += 1
        if len(item["examples"]) < int(config_section("weights").get("max_examples", 5)):
            item["examples"].append(
                {
                    "document": row.get("title") or row.get("document_title"),
                    "issuer": row.get("issuer"),
                    "source": row.get("source"),
                    "file_role": row.get("file_role"),
                    "page": row.get("page_start"),
                    "pasal": row.get("pasal"),
                    "evidence_source": source,
                }
            )
    if alias_of:
        item["alias_of"].add(alias_of)

def title_phrase_candidates(title: str) -> list[str]:
    title = lexicon_normalize_phrase(title)
    pieces = re.split(r"\s+(?:tentang|perihal)\s+|[-:–—]|;|\|", title, flags=re.IGNORECASE)
    phrases = [lexicon_normalize_phrase(piece) for piece in pieces]
    lowered = title.lower()
    pattern_phrases: list[str] = []
    for pattern in LEXICON_CONFIG.get("title_phrase_patterns") or []:
        for match in re.finditer(pattern, lowered, flags=re.IGNORECASE):
            pattern_phrases.append(lexicon_normalize_phrase(match.group(0)))
    return unique_keep_order([phrase for phrase in [*phrases, *pattern_phrases] if phrase])

def heading_phrase_candidates(heading: str) -> list[str]:
    extraction = config_section("extraction")
    heading = lexicon_normalize_phrase(heading)
    if not heading or not lexicon_phrase_valid(heading):
        return []
    if len(tokenize(heading)) > int(extraction.get("heading_max_tokens", 7)):
        return []
    return [heading]

def alias_pairs_from_text(text: str) -> list[tuple[str, str]]:
    extraction = config_section("extraction")
    pairs: list[tuple[str, str]] = []
    alias_trigger_regex = str(extraction.get("alias_trigger_regex", r"disingkat|disebut|\([A-Z0-9][A-Z0-9./-]{1,20}\)"))
    if not re.search(alias_trigger_regex, text):
        return pairs
    for sentence in re.split(r"(?<=[.;:])\s+", text):
        if not re.search(alias_trigger_regex, sentence):
            continue
        sentence = sentence[: int(extraction.get("alias_sentence_max_chars", 400))]
        for pattern in extraction.get("alias_patterns") or []:
            for match in re.finditer(pattern, sentence):
                long_phrase = lexicon_normalize_phrase(match.group("long"))
                alias = lexicon_normalize_phrase(match.group("alias"))
                if lexicon_phrase_valid(long_phrase) and lexicon_phrase_valid(alias):
                    pairs.append((long_phrase, alias))
    return pairs

def definition_phrases_from_text(text: str) -> list[str]:
    extraction = config_section("extraction")
    phrases: list[str] = []
    for match in re.finditer(str(extraction.get("definition_regex", r"(?:^|\s)(?:\d+\.\s*)?(?P<term>[A-ZÁÉÍÓÚÄËÏÖÜa-z0-9][^.;:\n]{3,120}?)\s+adalah\s+")), text):
        phrases.append(lexicon_normalize_phrase(match.group("term")))
    return phrases

def materialize_lexicon_candidates(candidates: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    weights = config_section("weights")
    rows: list[dict[str, Any]] = []
    for item in candidates.values():
        score = item["score"]
        source_keys = set(item["sources"].keys())
        if source_keys == {"heading"}:
            score *= float(weights.get("heading_only_multiplier", 0.1))
        if item["file_roles"].get("primary_regulation"):
            score += float(weights.get("primary_regulation_bonus", 2.0))
        if item["issuers"]:
            score += min(float(weights.get("issuer_bonus_max", 2.0)), len(item["issuers"]))
        confidence = "high" if score >= float(weights.get("high_confidence_min_score", 16)) else "medium" if score >= float(weights.get("medium_confidence_min_score", 8)) else "low"
        rows.append(
            {
                "phrase": item["phrase"],
                "type": item["type"],
                "score": round(score, 3),
                "confidence": confidence,
                "support_count": item["support_count"],
                "sources": dict(item["sources"]),
                "issuers": dict(item["issuers"]),
                "file_roles": dict(item["file_roles"]),
                "aliases": sorted(item["aliases"]),
                "alias_of": sorted(item["alias_of"]),
                "examples": item["examples"],
            }
        )
    rows.sort(key=lambda row: (row["type"], -row["score"], row["phrase"].lower()))
    return rows

def generated_lexicon_from_candidates(rows: list[dict[str, Any]], min_score: float, min_support: int) -> dict[str, Any]:
    entities: list[dict[str, Any]] = []
    topics: list[dict[str, Any]] = []
    aliases_by_parent: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        for parent in row.get("alias_of") or []:
            aliases_by_parent[parent].append(row["phrase"])

    for row in rows:
        if row["score"] < min_score or row["support_count"] < min_support:
            continue
        if set(row.get("sources", {}).keys()) == {"heading"}:
            continue
        phrase = row["phrase"]
        if row["type"] == "entity":
            patterns = unique_keep_order([phrase, *aliases_by_parent.get(phrase, [])])
            entities.append(
                {
                    "name": slugify(phrase).replace("-", "_"),
                    "patterns": patterns,
                    "expansions": [phrase],
                    "exact_phrases": patterns,
                    "generated": True,
                    "approved": False,
                    "review_notes": "",
                    "confidence": row["confidence"],
                    "support_count": row["support_count"],
                }
            )
        elif row["type"] == "topic":
            topics.append(
                {
                    "name": slugify(phrase).replace("-", "_"),
                    "patterns": [phrase],
                    "expansions": [phrase],
                    "exact_phrases": [phrase],
                    "generated": True,
                    "approved": False,
                    "review_notes": "",
                    "confidence": row["confidence"],
                    "support_count": row["support_count"],
                }
            )
    weights = config_section("weights")
    return {
        "entities": entities[: int(weights.get("generated_entities_limit", 300))],
        "topics": topics[: int(weights.get("generated_topics_limit", 300))],
        "aliases": dict(aliases_by_parent),
    }

def write_lexicon_candidates_report(rows: list[dict[str, Any]], path: Path, limit_per_type: int) -> None:
    lines = [
        "# Lexicon Candidates",
        "",
        f"- Candidates: {len(rows)}",
        "- Source: deterministic extraction from titles, metadata, headings, Pasal 1 definitions, and alias patterns.",
        "- This is a review artifact; it is not automatically trusted as legal truth.",
        "",
    ]
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_type[row["type"]].append(row)
    for candidate_type in ("entity", "topic", "alias"):
        values = by_type.get(candidate_type, [])[:limit_per_type]
        lines.extend([f"## {candidate_type.title()} Candidates", ""])
        for row in values:
            issuers = ", ".join(row["issuers"].keys()) or "-"
            sources = ", ".join(f"{key}:{value}" for key, value in row["sources"].items())
            lines.append(f"### {row['phrase']}")
            lines.append("")
            lines.append(f"- Score: `{row['score']}` / confidence `{row['confidence']}` / support `{row['support_count']}`")
            lines.append(f"- Issuers: `{issuers}`")
            lines.append(f"- Evidence sources: `{sources}`")
            if row.get("alias_of"):
                lines.append(f"- Alias of: `{', '.join(row['alias_of'])}`")
            if row["examples"]:
                example = row["examples"][0]
                lines.append(f"- Example: `{example.get('issuer')}` `{example.get('document')}` page `{example.get('page')}`")
            lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def cmd_extract_lexicon_candidates(args: argparse.Namespace) -> None:
    weights = config_section("weights")
    extraction = config_section("extraction")
    LEXICON_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    canonical_rows = read_ndjson_file(PROCESSED_DIR / "canonical_regulations.ndjson")
    extracted_rows = read_ndjson_file(PROCESSED_DIR / "extracted_documents.ndjson")

    for row in canonical_rows:
        title = row.get("title") or ""
        for phrase in title_phrase_candidates(title):
            add_lexicon_candidate(candidates, phrase, lexicon_candidate_type(phrase), "title", float(weights.get("title", 8.0)), row)
        for value in row.get("group_path") or []:
            for phrase in title_phrase_candidates(value):
                add_lexicon_candidate(candidates, phrase, lexicon_candidate_type(phrase), "metadata_group_path", float(weights.get("metadata_group_path", 3.0)), row)
        for key in ("sector", "sub_sector", "regulation_type"):
            if row.get(key):
                add_lexicon_candidate(candidates, str(row[key]), "topic", f"metadata_{key}", float(weights.get("metadata_field", 2.0)), row)

    for row in extracted_rows:
        title = row.get("title") or ""
        for phrase in title_phrase_candidates(title):
            add_lexicon_candidate(candidates, phrase, lexicon_candidate_type(phrase), "extracted_title", float(weights.get("extracted_title", 5.0)), row)

    scanned_blocks = 0
    for row in iter_ndjson_file(PROCESSED_DIR / "blocks.ndjson"):
        if args.max_blocks and scanned_blocks >= args.max_blocks:
            break
        scanned_blocks += 1
        if row.get("file_role") not in {"primary_regulation", "attachment", "operational_requirement"}:
            continue
        for heading in row.get("heading_path") or []:
            for phrase in heading_phrase_candidates(heading):
                add_lexicon_candidate(candidates, phrase, lexicon_candidate_type(phrase), "heading", float(weights.get("heading", 2.0)), row)
        text = row.get("text") or ""
        definition_like = row.get("pasal") == "Pasal 1" or " adalah " in text[: int(extraction.get("definition_detection_chars", 1200))].lower()
        if definition_like:
            for phrase in definition_phrases_from_text(text[: int(extraction.get("definition_scan_chars", 2500))]):
                add_lexicon_candidate(candidates, phrase, lexicon_candidate_type(phrase), "definition", float(weights.get("definition", 8.0)), row)
        if definition_like or row.get("page_start") in set(extraction.get("alias_scan_pages") or [1, 2, 3]):
            for long_phrase, alias in alias_pairs_from_text(text[: int(extraction.get("definition_scan_chars", 2500))]):
                add_lexicon_candidate(candidates, long_phrase, lexicon_candidate_type(long_phrase), "alias_definition", float(weights.get("alias_definition", 7.0)), row)
                add_lexicon_candidate(candidates, alias, "alias", "alias", float(weights.get("alias", 7.0)), row, alias_of=long_phrase)

    rows = materialize_lexicon_candidates(candidates)
    if args.min_score:
        rows = [row for row in rows if row["score"] >= args.min_score]
    LEXICON_CANDIDATES_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    generated = generated_lexicon_from_candidates(rows, min_score=args.generated_min_score, min_support=args.generated_min_support)
    GENERATED_LEXICON_PATH.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_lexicon_candidates_report(rows, REPORTS_DIR / "lexicon_candidates.md", args.report_limit)
    print(f"Wrote {LEXICON_CANDIDATES_PATH.relative_to(ROOT)} ({len(rows)} candidates; scanned {scanned_blocks} blocks)")
    print(f"Wrote {GENERATED_LEXICON_PATH.relative_to(ROOT)}")
    print("Wrote reports/lexicon_candidates.md")
