from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .normalization import normalize_extracted_text


def legal_unit_for_block(block: dict[str, Any]) -> dict[str, Any]:
    """Return the required structural payload for a corpus block."""
    legal_unit = block.get("legal_unit")
    if not isinstance(legal_unit, dict):
        raise ValueError("Corpus blocks must include a legal_unit mapping")
    return dict(legal_unit)


def legal_path_for_block(block: dict[str, Any]) -> dict[str, Any]:
    """Return the required explicit legal path without prose inference."""
    legal_unit = legal_unit_for_block(block)
    path = legal_unit.get("legal_path") or block.get("legal_path")
    if not isinstance(path, dict):
        raise ValueError("Corpus blocks must include a legal_path mapping")
    return dict(path)


def legal_path_labels(path: dict[str, Any]) -> list[str]:
    """Convert a structural legal path to the stable API display sequence."""

    return [
        str(path[level])
        for level in (
            "bab",
            "section",
            "point",
            "subpoint",
            "item",
            "bagian",
            "paragraf",
            "pasal",
            "ayat",
            "huruf",
            "angka",
        )
        if path.get(level)
    ]


def legal_unit_contract(block: dict[str, Any]) -> dict[str, Any]:
    """Copy the required portable legal-node contract into a normalized row."""

    legal_unit = legal_unit_for_block(block)

    legal_path = legal_path_for_block(block)
    raw_anchors = block.get("anchors")
    anchors = [dict(raw_anchors)] if isinstance(raw_anchors, Mapping) else raw_anchors
    source_spans = legal_unit.get("source_spans")
    return {
        "node_id": block.get("node_id"),
        "document_part": block.get("document_part") or legal_unit.get("document_part"),
        "parent_id": block.get("parent_id"),
        "previous_id": block.get("previous_id"),
        "anchors": anchors,
        "source_spans": source_spans,
        "legal_unit": legal_unit,
        "citation_admission": block.get("citation_admission"),
        "legal_path": legal_path,
        "continuation": legal_unit.get("continuation"),
        "source_block_ids": block.get("source_block_ids") or [],
        "unit_path": legal_path_labels(legal_path),
        "assembled_text": block.get("assembled_text") or block.get("retrieval_text"),
    }


def source_priority_for_role(file_role: str | None) -> str:
    if file_role in {"primary_regulation", "attachment", "operational_requirement"}:
        return "primary"
    if file_role in {"secondary_faq", "secondary_summary"}:
        return "secondary"
    return "unknown"


def section_type_for_block(block: dict[str, Any]) -> str:
    block_type = block.get("block_type")
    file_role = block.get("file_role")
    if file_role == "attachment":
        return "attachment"
    if file_role == "secondary_faq" or block_type == "qa_or_faq":
        return "faq"
    if file_role == "secondary_summary":
        return "abstrak"
    if block_type == "heading":
        return "heading"
    if block_type == "table_or_row":
        return "table"
    legal_unit = legal_unit_for_block(block)
    return str(legal_unit["type"])


def citation_quality_for_block(block: dict[str, Any]) -> str:
    legal_path = legal_path_for_block(block)
    pasal = legal_path.get("pasal")
    ayat = legal_path.get("ayat")
    huruf = legal_path.get("huruf")
    has_document = bool(block.get("document_title") or (block.get("citation") or {}).get("document"))
    if not has_document:
        return "missing_document"
    if block.get("page_start") and pasal and ayat and huruf:
        return "document_page_pasal_ayat_huruf"
    if block.get("page_start") and pasal and ayat:
        return "document_page_pasal_ayat"
    if block.get("page_start") and pasal:
        return "document_page_pasal"
    if block.get("page_start") and legal_path.get("section"):
        return "document_page_section"
    if block.get("page_start"):
        return "document_page"
    return "document_only"


def citation_text_for_block(block: dict[str, Any]) -> str:
    legal_path = legal_path_for_block(block)
    parts = [block.get("document_title") or (block.get("citation") or {}).get("document") or "Dokumen tidak diketahui"]
    if block.get("page_start"):
        parts.append(f"hlm. {block['page_start']}")
    if legal_path.get("section"):
        parts.append(str(legal_path["section"]))
    if legal_path.get("point"):
        parts.append(f"butir {legal_path['point']}")
    if legal_path.get("subpoint"):
        parts.append(f"subbutir {legal_path['subpoint']}")
    if legal_path.get("item"):
        parts.append(f"item {legal_path['item']}")
    if legal_path.get("pasal"):
        parts.append(str(legal_path["pasal"]))
    if legal_path.get("ayat"):
        parts.append(f"ayat {legal_path['ayat']}")
    if legal_path.get("huruf"):
        parts.append(str(legal_path["huruf"]))
    if legal_path.get("angka"):
        parts.append(f"angka {legal_path['angka']}")
    return ", ".join(parts)


def normalize_source_corpus_block(
    block: dict[str, Any],
    regulation_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    regulation_metadata = regulation_metadata or {}

    def value(name: str, default: Any = None) -> Any:
        return block.get(name, regulation_metadata.get(name, default))

    citation_quality = citation_quality_for_block(block)
    display_text = normalize_extracted_text(str(block.get("display_text") or ""), block.get("block_type"))
    retrieval_text = normalize_extracted_text(str(block.get("retrieval_text") or ""), block.get("block_type"))
    legal_path = legal_path_for_block(block)
    row = {
        "block_id": block.get("block_id"),
        "canonical_id": value("canonical_id"),
        "file_id": block.get("file_id"),
        "issuer": block.get("issuer"),
        "hosting_source_issuer": block.get("hosting_source_issuer"),
        "issuer_resolution_basis": block.get("issuer_resolution_basis"),
        "issuer_differs_from_host": block.get("issuer_differs_from_host", False),
        "source": block.get("source"),
        "source_priority": source_priority_for_role(block.get("file_role")),
        "file_role": block.get("file_role"),
        "searchable_primary": block.get("searchable_primary", True),
        "primary_duplicate_status": block.get("primary_duplicate_status"),
        "primary_duplicate_group_id": block.get("primary_duplicate_group_id"),
        "primary_duplicate_of_file_id": block.get("primary_duplicate_of_file_id"),
        "primary_duplicate_group_size": block.get("primary_duplicate_group_size"),
        "primary_duplicate_reason": block.get("primary_duplicate_reason"),
        "document_id": block.get("canonical_id"),
        "document_title": block.get("document_title"),
        "regulation_type": value("regulation_type"),
        "number": value("number"),
        "year": value("year"),
        "regulation_version_key": value("regulation_version_key", value("canonical_id")),
        "regulation_series_key": value("regulation_series_key"),
        "issued_date": value("issued_date"),
        "effective_date": value("effective_date"),
        "repeal_date": value("repeal_date"),
        "lifecycle_status": value("lifecycle_status"),
        "is_current": value("is_current"),
        "supersedes": value("supersedes", []),
        "amends": value("amends", []),
        "page": block.get("page_start"),
        "page_start": block.get("page_start"),
        "page_end": block.get("page_end"),
        "section_type": section_type_for_block(block),
        "block_type": block.get("block_type"),
        "table_readability": block.get("table_readability"),
        "extraction_method": block.get("extraction_method") or "markdown",
        "heading_path": block.get("heading_path") or [],
        "pasal": legal_path.get("pasal"),
        "ayat": legal_path.get("ayat"),
        "huruf": legal_path.get("huruf"),
        "text": display_text,
        "text_markdown": block.get("text_markdown"),
        "text_geometry": block.get("text_geometry"),
        "citation": {
            "document": block.get("document_title"),
            "page": block.get("page_start"),
            "pasal": legal_path.get("pasal"),
            "ayat": legal_path.get("ayat"),
            "huruf": legal_path.get("huruf"),
            "angka": legal_path.get("angka"),
            "text": citation_text_for_block(block),
            "quality": citation_quality,
        },
        "citation_quality": citation_quality,
        "citation_policy": {
            "primary_first": True,
            "best_effort_fields": ["document", "page", "pasal", "ayat", "huruf"],
            "must_say_not_found_when_unsure": True,
        },
    }
    row.update(legal_unit_contract(block))
    row["display_text"] = display_text
    row["retrieval_text"] = retrieval_text
    row["assembled_text"] = str(block.get("assembled_text") or retrieval_text)
    return row
