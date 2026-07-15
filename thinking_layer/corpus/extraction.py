"""Raw LiteParse helpers and the v2-only legal-unit corpus adapter."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from ..common.text import normalize_space, slugify
from ..config.heuristics import heuristic_section
from ..config.paths import RAW_LITEPARSE_DIR
from .legal_units import CHUNK_SCHEMA_VERSION, parse_legal_units
from .metadata import short_hash
from .normalization import markdown_table_rows


_MOJIBAKE_RE = re.compile(r"(?:\ufffd|â[^\s]{0,3}|Ã[^\s]{0,3}|Â[^\s]{0,3})")
_OUTLINE_ATOMIC_TYPES = {"point", "subpoint", "item"}
_MAX_OUTLINE_ATOMIC_CHARS = 1_800


def is_seojk_outline_document(manifest: dict[str, Any]) -> bool:
    regulation_type = str(manifest.get("regulation_type") or "").casefold()
    return "seojk" in regulation_type or "surat edaran ojk" in regulation_type


def table_readability(text: str) -> dict[str, Any]:
    """Return deterministic evidence-readability metadata for a table unit.

    Tables remain in extraction output for auditability.  Only tables with a
    minimally coherent row/cell structure and enough natural-language labels
    are citation eligible; formula fragments and encoding corruption are
    quarantined.
    """
    rows = markdown_table_rows(text)
    nonempty_cells = [cell for row in rows for cell in row if normalize_space(cell)]
    plain_text = normalize_space(" ".join(nonempty_cells))
    natural_words = re.findall(r"(?i)(?<!\w)[a-zÀ-ÿ]{3,}(?!\w)", plain_text)
    formula_symbols = re.findall(r"[=∑√×÷±^]", plain_text)
    reasons: list[str] = []
    if _MOJIBAKE_RE.search(plain_text):
        reasons.append("mojibake")
    if len(rows) < 3 or len(nonempty_cells) < 4:
        reasons.append("insufficient_table_structure")
    if len(re.findall(r"(?m)^[HD]\|[A-Z0-9]", text)) >= 2:
        reasons.append("record_code_fragment")
    if len(natural_words) < 4:
        reasons.append("insufficient_natural_language")
    if len(formula_symbols) >= 2 and len(natural_words) < 10:
        reasons.append("formula_dominant")
    return {
        "status": "readable" if not reasons else "quarantined",
        "is_readable": not reasons,
        "reasons": reasons,
        "row_count": len(rows),
        "nonempty_cell_count": len(nonempty_cells),
        "natural_word_count": len(natural_words),
        "formula_symbol_count": len(formula_symbols),
    }


def safe_text(value: str | None) -> str:
    return normalize_space(value).replace("\x00", "")


def word_box_to_json(word: Any) -> dict[str, Any]:
    return {
        "text": getattr(word, "text", "") or "",
        "x": getattr(word, "x", None),
        "y": getattr(word, "y", None),
        "width": getattr(word, "width", None),
        "height": getattr(word, "height", None),
    }


def text_item_to_json(item: Any) -> dict[str, Any]:
    return {
        "text": getattr(item, "text", "") or "",
        "x": getattr(item, "x", None),
        "y": getattr(item, "y", None),
        "width": getattr(item, "width", None),
        "height": getattr(item, "height", None),
        "font_name": getattr(item, "font_name", None),
        "font_size": getattr(item, "font_size", None),
        "confidence": getattr(item, "confidence", None),
        "rotation": getattr(item, "rotation", None),
        "words": [word_box_to_json(word) for word in (getattr(item, "words", []) or [])],
    }


def raw_output_path(file_id: str) -> Path:
    config = heuristic_section("extraction_heuristics", "raw_output")
    return RAW_LITEPARSE_DIR / f"{slugify(file_id)[: int(config.get('slug_max_chars', 160))]}-{short_hash(file_id)}.json"


def page_to_json(page: Any) -> dict[str, Any]:
    """Preserve LiteParse page text and geometry unchanged for future parses."""
    text_items = getattr(page, "text_items", []) or []
    return {
        "page_num": getattr(page, "page_num", None),
        "width": getattr(page, "width", None),
        "height": getattr(page, "height", None),
        "text": getattr(page, "text", "") or "",
        "markdown": getattr(page, "markdown", "") or "",
        "text_item_count": len(text_items),
        "text_items": [text_item_to_json(item) for item in text_items],
    }


def classify_extraction_status(pages: list[dict[str, Any]], total_text_len: int) -> tuple[str, str | None]:
    config = heuristic_section("extraction_heuristics", "ocr_status")
    if not pages:
        return "parse_failed", "no_pages_returned"
    empty_pages = sum(
        1
        for page in pages
        if len(safe_text(page.get("text") or page.get("markdown")))
        < int(config.get("empty_page_text_chars", 20))
    )
    empty_ratio = empty_pages / len(pages)
    if total_text_len < int(config.get("total_text_min_chars", 100)):
        return "likely_needs_ocr", "document_text_under_100_chars"
    if empty_ratio > float(config.get("empty_page_ratio_threshold", 0.70)):
        return "likely_needs_ocr", "more_than_70_percent_pages_empty"
    return "extracted_ok", None


def extract_blocks(manifest: dict[str, Any], pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Emit the sole v2 corpus block contract from ordered raw page text.

    The parser owns legal structure, source anchors, and deterministic IDs.
    This adapter owns manifest provenance and the explicit evidence-admission
    policy: atomic legal leaves plus bounded enumeration aggregates.  It never
    invokes sentence splitting or attempts to infer citations from prose.
    """
    blocks: list[dict[str, Any]] = []
    nodes = parse_legal_units(
        pages,
        document_id=str(manifest["file_id"]),
        enable_outline=is_seojk_outline_document(manifest),
    )
    parent_ids = {node.get("parent_id") for node in nodes if node.get("parent_id")}
    for node in nodes:
        legal_path = node.get("legal_path") or {}
        legal_unit = node.get("legal_unit") or {}
        unit_type = str(node.get("unit_type") or legal_unit.get("type") or "")
        legal_unit_role = str(node.get("legal_unit_role") or legal_unit.get("role") or "")
        document_part = str(node.get("document_part") or legal_unit.get("document_part") or "")
        is_enumeration_aggregate = (
            unit_type == "enumeration_aggregate" and legal_unit_role == "enumeration_aggregate"
        )
        is_outline_leaf = (
            unit_type in _OUTLINE_ATOMIC_TYPES
            and node.get("node_id") not in parent_ids
            and bool(legal_path.get("section"))
            and (
                document_part == "normative"
                or (document_part == "attachment" and legal_path.get("bab") == "BAB I")
            )
            and node.get("page_start") == node.get("page_end")
            and 40 <= len(str(node.get("display_text") or "")) <= _MAX_OUTLINE_ATOMIC_CHARS
        )
        is_atomic_leaf = (
            unit_type in {"pasal", "ayat", "huruf", "angka", "table"}
            and node.get("node_id") not in parent_ids
        ) or is_outline_leaf
        if not (is_atomic_leaf or is_enumeration_aggregate):
            continue

        heading_path = [
            str(legal_path[level])
            for level in ("bab", "section", "point", "subpoint", "bagian", "paragraf")
            if legal_path.get(level)
        ]
        display_text = str(node.get("display_text") or "")
        readability = table_readability(display_text) if unit_type == "table" else None
        is_quarantined_table = bool(readability and not readability["is_readable"])
        has_dangling_reference = bool(
            re.search(
                r"\b(?:(?:pada|dalam|di)\s+)?(?:ayat|Pasal|huruf)\s*$",
                display_text,
                re.IGNORECASE,
            )
        )
        quarantine_reason = (
            "unreadable_table"
            if is_quarantined_table
            else "non_evidence_document_part"
            if document_part == "promulgation"
            else "dangling_legal_reference"
            if has_dangling_reference
            else None
        )
        citation_admission = (
            f"quarantined_{quarantine_reason}"
            if quarantine_reason
            else "enumeration_aggregate"
            if is_enumeration_aggregate
            else "atomic_leaf"
        )
        blocks.append(
            {
                **node,
                "chunk_schema_version": CHUNK_SCHEMA_VERSION,
                "canonical_id": manifest["canonical_id"],
                "file_id": manifest["file_id"],
                "source": manifest["source"],
                "issuer": manifest["issuer"],
                "hosting_source_issuer": manifest.get("hosting_source_issuer"),
                "issuer_resolution_basis": manifest.get("issuer_resolution_basis"),
                "issuer_differs_from_host": manifest.get("issuer_differs_from_host", False),
                "file_role": manifest["file_role"],
                "document_title": manifest["title"],
                "regulation_type": manifest.get("regulation_type"),
                "number": manifest.get("number"),
                "year": manifest.get("year"),
                "regulation_version_key": manifest.get("regulation_version_key"),
                "regulation_series_key": manifest.get("regulation_series_key"),
                "issued_date": manifest.get("issued_date"),
                "effective_date": manifest.get("effective_date"),
                "repeal_date": manifest.get("repeal_date"),
                "lifecycle_status": manifest.get("lifecycle_status"),
                "is_current": manifest.get("is_current"),
                "supersedes": manifest.get("supersedes") or [],
                "amends": manifest.get("amends") or [],
                "searchable_primary": manifest.get("searchable_primary", True),
                "primary_duplicate_status": manifest.get("primary_duplicate_status"),
                "primary_duplicate_group_id": manifest.get("primary_duplicate_group_id"),
                "primary_duplicate_of_file_id": manifest.get("primary_duplicate_of_file_id"),
                "primary_duplicate_group_size": manifest.get("primary_duplicate_group_size"),
                "primary_duplicate_reason": manifest.get("primary_duplicate_reason"),
                "block_type": "table_or_row" if unit_type == "table" else "legal_unit",
                "extraction_method": "legal_units_v2",
                "citation_admission": citation_admission,
                "citation_quarantine": (
                    {
                        "reason": quarantine_reason,
                        "details": readability if is_quarantined_table else None,
                    }
                    if quarantine_reason
                    else None
                ),
                "table_readability": readability,
                "heading_path": heading_path,
                "pasal": legal_path.get("pasal"),
                "ayat": legal_path.get("ayat"),
                "huruf": legal_path.get("huruf"),
                "angka": legal_path.get("angka"),
                "text": display_text,
                "text_markdown": display_text,
                "text_geometry": None,
                "citation": {
                    "document": manifest["title"],
                    "page": node.get("page_start"),
                    "pasal": legal_path.get("pasal"),
                    "ayat": legal_path.get("ayat"),
                    "huruf": legal_path.get("huruf"),
                    "angka": legal_path.get("angka"),
                },
                "confidence": {
                    "page": "high" if node.get("page_start") is not None else "missing",
                    "pasal": "high" if legal_path.get("pasal") else "missing",
                    "ayat": "high" if legal_path.get("ayat") else "missing",
                    "huruf": "high" if legal_path.get("huruf") else "missing",
                    "angka": "high" if legal_path.get("angka") else "missing",
                },
            }
        )
    return blocks
