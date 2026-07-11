from __future__ import annotations

from typing import Any

from .normalization import normalize_extracted_text


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
    if block.get("ayat"):
        return "ayat"
    if block.get("pasal") or block_type == "article":
        return "pasal"
    if block_type == "list_item":
        return "list_item"
    return "paragraph"


def citation_quality_for_block(block: dict[str, Any]) -> str:
    has_document = bool(block.get("document_title") or (block.get("citation") or {}).get("document"))
    if not has_document:
        return "missing_document"
    if block.get("page_start") and block.get("pasal") and block.get("ayat") and block.get("huruf"):
        return "document_page_pasal_ayat_huruf"
    if block.get("page_start") and block.get("pasal") and block.get("ayat"):
        return "document_page_pasal_ayat"
    if block.get("page_start") and block.get("pasal"):
        return "document_page_pasal"
    if block.get("page_start"):
        return "document_page"
    return "document_only"


def citation_text_for_block(block: dict[str, Any]) -> str:
    parts = [block.get("document_title") or (block.get("citation") or {}).get("document") or "Dokumen tidak diketahui"]
    if block.get("page_start"):
        parts.append(f"hlm. {block['page_start']}")
    if block.get("pasal"):
        parts.append(str(block["pasal"]))
    if block.get("ayat"):
        parts.append(f"ayat {block['ayat']}")
    if block.get("huruf"):
        parts.append(str(block["huruf"]))
    return ", ".join(parts)


def normalize_source_corpus_block(
    block: dict[str, Any],
    regulation_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    regulation_metadata = regulation_metadata or {}

    def value(name: str, default: Any = None) -> Any:
        return block.get(name, regulation_metadata.get(name, default))

    citation_quality = citation_quality_for_block(block)
    text = normalize_extracted_text(str(block.get("text") or ""), block.get("block_type"))
    return {
        "block_id": block.get("block_id"),
        "canonical_id": value("canonical_id"),
        "file_id": block.get("file_id"),
        "issuer": block.get("issuer"),
        "source": block.get("source"),
        "source_priority": source_priority_for_role(block.get("file_role")),
        "file_role": block.get("file_role"),
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
        "extraction_method": block.get("extraction_method") or "markdown",
        "heading_path": block.get("heading_path") or [],
        "pasal": block.get("pasal"),
        "ayat": block.get("ayat"),
        "huruf": block.get("huruf"),
        "text": text,
        "text_markdown": block.get("text_markdown"),
        "text_geometry": block.get("text_geometry"),
        "citation": {
            "document": block.get("document_title"),
            "page": block.get("page_start"),
            "pasal": block.get("pasal"),
            "ayat": block.get("ayat"),
            "huruf": block.get("huruf"),
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
