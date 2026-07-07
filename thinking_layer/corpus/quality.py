from __future__ import annotations

from typing import Any

from ..common.text import normalize_space


def extraction_issue_flags(row: dict[str, Any]) -> list[str]:
    text = normalize_space(str(row.get("text") or row.get("snippet") or ""))
    flags = []
    if not row.get("document_title") and not (row.get("citation") or {}).get("document"):
        flags.append("missing_document_title")
    if not row.get("page_start") and not (row.get("citation") or {}).get("page"):
        flags.append("missing_page")
    if "|---" in text:
        flags.append("markdown_table_artifact")
    if "![](" in text:
        flags.append("image_placeholder")
    if len(text) < 30:
        flags.append("very_short_text")
    if "................" in text or "................................" in text:
        flags.append("form_placeholder_text")
    return flags
