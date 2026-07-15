from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Iterable

from ..common.io import iter_ndjson_file
from ..config.paths import PROCESSED_DIR, REPORTS_DIR, SOURCE_CORPUS_PATH
from .extraction import table_readability


ACCEPTED_CITATION_ADMISSIONS = {"atomic_leaf", "enumeration_aggregate"}
_DANGLING_REFERENCE_RE = re.compile(
    r"\b(?:(?:pada|dalam|di)\s+)?(?:ayat|Pasal|huruf)\s*$",
    re.IGNORECASE,
)
_URL_CONTAMINATION_RE = re.compile(r"https?://(?:www\.)?jdih\.ojk\.go\.id/?", re.IGNORECASE)
_EXPLANATION_CONTAMINATION_RE = re.compile(
    r"(?:^\s*(?:Pasal\s+\d+[A-Z]?\s+)?Cukup\s+jelas\.?\s*$|\bAgar\s+setiap\s+orang\s+mengetahuinya\b)",
    re.IGNORECASE,
)
_EXPECTED_ISSUER = {
    "PBI": "BI",
    "PADG": "BI",
    "POJK": "OJK",
    "SEOJK": "OJK",
}
_CHECK_NAMES = (
    "missing_legal_unit_provenance",
    "dangling_legal_reference",
    "oversized_normative_pasal",
    "url_contamination",
    "empty_legal_path",
    "issuer_instrument_mismatch",
    "suppressed_duplicate_leakage",
    "unreadable_table_citation_admission",
    "document_part_contamination",
)


def _identity(row: dict[str, Any], fallback: str) -> tuple[str, str]:
    return str(row.get("file_id") or ""), str(row.get("block_id") or row.get("node_id") or fallback)


def _unit_type(row: dict[str, Any]) -> str:
    return str(
        row.get("unit_type")
        or (row.get("legal_unit") or {}).get("type")
        or row.get("section_type")
        or ""
    )


def _legal_path(row: dict[str, Any]) -> dict[str, Any] | None:
    value = row.get("legal_path") or (row.get("legal_unit") or {}).get("legal_path")
    return value if isinstance(value, dict) else None


def _document_part(row: dict[str, Any]) -> str | None:
    value = row.get("document_part") or (row.get("legal_unit") or {}).get("document_part")
    return str(value) if value else None


def _display_text(row: dict[str, Any]) -> str:
    return str(row.get("display_text") or row.get("text") or "")


def _example(row: dict[str, Any], *, layer: str | None = None, reason: str | None = None) -> dict[str, Any]:
    item = {
        "file_id": row.get("file_id"),
        "block_id": row.get("block_id") or row.get("node_id"),
        "page": row.get("page_start") or row.get("page"),
    }
    if layer:
        item["layer"] = layer
    if reason:
        item["reason"] = reason
    return item


def _missing_provenance(row: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not row.get("node_id"):
        missing.append("node_id")
    if not isinstance(row.get("legal_unit"), dict):
        missing.append("legal_unit")
    if not row.get("source_block_ids"):
        missing.append("source_block_ids")
    if not row.get("anchors"):
        missing.append("anchors")
    if not _display_text(row):
        missing.append("display_text")
    if not row.get("retrieval_text"):
        missing.append("retrieval_text")
    if not _document_part(row):
        missing.append("document_part")
    source_spans = (row.get("legal_unit") or {}).get("source_spans") or row.get("source_spans")
    if not source_spans:
        missing.append("source_spans")
    return missing


def _issuer_mismatch(row: dict[str, Any]) -> str | None:
    regulation_type = str(row.get("regulation_type") or "").upper()
    instrument = next((kind for kind in _EXPECTED_ISSUER if kind in regulation_type), None)
    if not instrument:
        return None
    expected = _EXPECTED_ISSUER[instrument]
    actual = str(row.get("issuer") or "")
    return f"{instrument}_expected_{expected}_found_{actual or 'missing'}" if actual != expected else None


def audit_corpus_artifacts(
    blocks: Iterable[dict[str, Any]],
    source_rows: Iterable[dict[str, Any]],
    *,
    max_examples: int = 5,
) -> dict[str, Any]:
    checks = {
        name: {"count": 0, "blocking": True, "examples": []}
        for name in _CHECK_NAMES
    }

    def record(name: str, row: dict[str, Any], *, layer: str | None = None, reason: str | None = None) -> None:
        check = checks[name]
        check["count"] += 1
        if len(check["examples"]) < max_examples:
            check["examples"].append(_example(row, layer=layer, reason=reason))

    identities: set[tuple[str, str]] = set()
    block_identities: set[tuple[str, str]] = set()
    block_table_violations: set[tuple[str, str]] = set()
    blocks_scanned = 0
    source_rows_scanned = 0

    def inspect_semantic(row: dict[str, Any], *, admitted: bool, identity: tuple[str, str]) -> None:
        text = _display_text(row)
        path = _legal_path(row)
        unit_type = _unit_type(row)

        if admitted and unit_type in {"pasal", "ayat", "huruf", "angka"} and _DANGLING_REFERENCE_RE.search(text):
            record("dangling_legal_reference", row)

        page_start = row.get("page_start")
        page_end = row.get("page_end")
        page_delta = page_end - page_start if isinstance(page_start, int) and isinstance(page_end, int) else 0
        if (
            admitted
            and unit_type == "pasal"
            and (_document_part(row) or "normative") == "normative"
            and ((page_delta >= 2 and len(text) > 1_500) or len(text) > 3_000)
        ):
            record("oversized_normative_pasal", row, reason=f"page_delta={page_delta},chars={len(text)}")

        combined_text = " ".join(
            str(row.get(field) or "") for field in ("display_text", "retrieval_text", "text")
        )
        if _URL_CONTAMINATION_RE.search(combined_text):
            record("url_contamination", row)

        if admitted and not path:
            record("empty_legal_path", row)

        mismatch = _issuer_mismatch(row)
        if mismatch:
            record("issuer_instrument_mismatch", row, reason=mismatch)

        if unit_type == "table" and admitted:
            quality = row.get("table_readability") or table_readability(text)
            if not quality.get("is_readable", False):
                record(
                    "unreadable_table_citation_admission",
                    row,
                    reason=",".join(quality.get("reasons") or ["unreadable"]),
                )
                block_table_violations.add(identity)

        part = _document_part(row)
        if admitted and (
            part == "promulgation"
            or ((part in {None, "normative"}) and _EXPLANATION_CONTAMINATION_RE.search(text))
        ):
            record("document_part_contamination", row, reason=f"document_part={part or 'missing'}")

    for index, row in enumerate(blocks):
        blocks_scanned += 1
        identity = _identity(row, f"blocks-{index}")
        identities.add(identity)
        block_identities.add(identity)
        missing = _missing_provenance(row)
        if missing:
            record(
                "missing_legal_unit_provenance",
                row,
                layer="blocks",
                reason=",".join(missing),
            )
        inspect_semantic(
            row,
            admitted=row.get("citation_admission") in ACCEPTED_CITATION_ADMISSIONS,
            identity=identity,
        )

    for index, row in enumerate(source_rows):
        source_rows_scanned += 1
        identity = _identity(row, f"source_corpus-{index}")
        identities.add(identity)
        missing = _missing_provenance(row)
        if missing:
            record(
                "missing_legal_unit_provenance",
                row,
                layer="source_corpus",
                reason=",".join(missing),
            )
        if identity not in block_identities:
            inspect_semantic(row, admitted=True, identity=identity)
        if row.get("searchable_primary") is False or row.get("primary_duplicate_status") == "duplicate":
            record("suppressed_duplicate_leakage", row)
        if _unit_type(row) == "table" and identity not in block_table_violations:
            quality = row.get("table_readability") or table_readability(_display_text(row))
            if not quality.get("is_readable", False):
                record(
                    "unreadable_table_citation_admission",
                    row,
                    reason=",".join(quality.get("reasons") or ["unreadable"]),
                )

    failed = [name for name, check in checks.items() if check["blocking"] and check["count"]]
    return {
        "status": "fail" if failed else "pass",
        "summary": {
            "blocks_scanned": blocks_scanned,
            "source_rows_scanned": source_rows_scanned,
            "unique_units_scanned": len(identities),
            "failed_checks": len(failed),
            "blocking_violations": sum(checks[name]["count"] for name in failed),
        },
        "checks": checks,
    }


def cmd_corpus_audit(args: argparse.Namespace) -> None:
    blocks_path = Path(args.blocks) if args.blocks else PROCESSED_DIR / "blocks.ndjson"
    source_path = Path(args.source_corpus) if args.source_corpus else SOURCE_CORPUS_PATH
    for path in (blocks_path, source_path):
        if not path.exists():
            raise SystemExit(f"Missing audit input: {path}")

    report = audit_corpus_artifacts(
        iter_ndjson_file(blocks_path),
        iter_ndjson_file(source_path),
        max_examples=args.max_examples,
    )
    output_path = Path(args.output) if args.output else REPORTS_DIR / "corpus_audit.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    output_path.write_text(payload, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    if report["status"] == "fail" and not args.report_only:
        raise SystemExit(1)
