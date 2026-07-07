from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..config.heuristics import heuristic_section
from .metadata import short_hash
from ..config.paths import RAW_LITEPARSE_DIR
from ..common.text import normalize_space, slugify
from .geometry import geometry_text_for_block
from .normalization import markdown_table_rows, normalize_extracted_text, normalize_table_row


def safe_text(value: str | None) -> str:
    return normalize_space(value).replace("\x00", "")


def is_table_separator(line: str, config: dict[str, Any] | None = None) -> bool:
    config = config or heuristic_section("extraction_heuristics", "sentence_blocks")
    return bool(re.match(str(config.get("table_separator_regex")), line))


def is_markdown_table_row(line: str, config: dict[str, Any] | None = None) -> bool:
    config = config or heuristic_section("extraction_heuristics", "sentence_blocks")
    pipe_count = line.count("|")
    if pipe_count < int(config.get("table_row_min_pipes", 2)):
        return False
    return is_table_separator(line, config) or bool(re.search(r"\|\s*[^|]+\s*\|", line))


def starts_list_item(line: str) -> bool:
    config = heuristic_section("extraction_heuristics", "block_type")
    return bool(re.match(str(config.get("list_item_regex", r"^(\(?\d+[a-z]?\)|[a-z]\.|[ivxlcdm]+\.)\s+")), line, flags=re.IGNORECASE))


def sentence_like_blocks(text: str) -> list[str]:
    config = heuristic_section("extraction_heuristics", "sentence_blocks")
    lines = [normalize_space(line) for line in text.splitlines()]
    blocks: list[str] = []
    current: list[str] = []
    table_current: list[str] = []

    def flush() -> None:
        nonlocal current
        if current:
            blocks.append(normalize_space(" ".join(current)))
            current = []

    def flush_table() -> None:
        nonlocal table_current
        if table_current:
            blocks.append("\n".join(table_current))
            table_current = []

    for line in lines:
        if re.fullmatch(str(config.get("page_number_regex", r"-?\s*\d+\s*-?")), line):
            continue
        if not line:
            flush_table()
            if len(" ".join(current)) >= int(config.get("flush_on_blank_min_chars", 350)):
                flush()
            continue

        heading_config = heuristic_section("extraction_heuristics", "headings")
        if is_heading(line) or re.match(str(heading_config.get("pasal_heading_regex", r"^Pasal\s+\d+[A-Z]?\b")), line, flags=re.IGNORECASE):
            flush_table()
            flush()
            blocks.append(line)
            continue

        if bool(config.get("preserve_table_rows", True)) and is_markdown_table_row(line, config):
            flush()
            table_current.append(line)
            continue

        if bool(config.get("list_item_starts_new_block", True)) and starts_list_item(line):
            flush_table()
            flush()
            current.append(line)
            continue

        flush_table()
        current.append(line)
        current_text = " ".join(current)
        if len(current_text) >= int(config.get("hard_flush_min_chars", 1200)):
            flush()
        elif len(current_text) >= int(config.get("soft_flush_min_chars", 550)) and re.search(str(config.get("sentence_end_regex", r"[.;:]$")), line):
            flush()

    flush_table()
    flush()

    heading_config = heuristic_section("extraction_heuristics", "headings")
    pasal_heading_regex = str(heading_config.get("pasal_heading_regex", r"^Pasal\s+\d+[A-Z]?\b"))
    return [
        block
        for block in blocks
        if (
            len(block) > int(config.get("min_block_chars", 8))
            or is_heading(block)
            or re.match(pasal_heading_regex, block, flags=re.IGNORECASE)
        )
    ]


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


def is_heading(line: str) -> bool:
    config = heuristic_section("extraction_heuristics", "headings")
    compact = normalize_space(line)
    if not compact:
        return False
    for pattern in config.get("heading_regexes") or []:
        pattern_text = str(pattern)
        flags = 0 if pattern_text.startswith("^[A-Z]") else re.IGNORECASE
        if re.match(pattern_text, compact, flags=flags):
            return True
    return False


def detect_pasal(text: str, current_pasal: str | None = None) -> str | None:
    config = heuristic_section("extraction_heuristics", "citations")
    match = re.search(str(config.get("pasal_regex", r"\bPasal\s+(\d+[A-Z]?)\b")), text, flags=re.IGNORECASE)
    if match:
        if current_pasal and match.start() > 0:
            return current_pasal
        return f"Pasal {match.group(1)}"
    return current_pasal


def detect_ayat(text: str, current_ayat: str | None = None) -> str | None:
    config = heuristic_section("extraction_heuristics", "citations")
    match = re.match(str(config.get("ayat_start_regex", r"^\s*(?:Ayat\s*)?\((\d+[a-z]?)\)")), text, flags=re.IGNORECASE)
    if match:
        return f"({match.group(1)})"
    match = re.match(str(config.get("ayat_word_start_regex", r"^\s*Ayat\s+(\d+[a-z]?)\b")), text, flags=re.IGNORECASE)
    if match:
        return f"({match.group(1)})"
    if current_ayat:
        return None
    match = re.search(str(config.get("ayat_regex", r"(^|\s)\((\d+[a-z]?)\)")), text, flags=re.IGNORECASE)
    if match:
        return f"({match.group(2)})"
    match = re.search(str(config.get("ayat_word_regex", r"\bayat\s+(\d+[a-z]?)\b")), text, flags=re.IGNORECASE)
    if match:
        return f"({match.group(1)})"
    return None


def detect_huruf(text: str, allow_context_reference: bool = True) -> str | None:
    config = heuristic_section("extraction_heuristics", "citations")
    match = re.match(str(config.get("huruf_label_regex", r"^\s*Huruf\s+([a-z])\b")), text, flags=re.IGNORECASE)
    if match:
        return f"huruf {match.group(1).lower()}"
    match = re.match(str(config.get("huruf_list_regex", r"^\(?([a-z])\)?[.)]\s+")), text)
    if match:
        return f"huruf {match.group(1).lower()}"
    if allow_context_reference:
        match = re.search(
            str(config.get("huruf_context_regex", r"\bayat\s+\(?\d+[a-z]?\)?\s+huruf\s+([a-z])\b")),
            text,
            flags=re.IGNORECASE,
        )
        if match:
            return f"huruf {match.group(1).lower()}"
    return None


def detect_block_type(text: str, file_role: str) -> str:
    config = heuristic_section("extraction_heuristics", "block_type")
    if "|" in text and text.count("|") >= int(config.get("table_pipe_min_count", 4)):
        return "table_or_row"
    if re.search(str(config.get("article_regex", r"\bpasal\s+\d+[a-z]?\b")), text, flags=re.IGNORECASE):
        return "article"
    if "?" in text[: int(config.get("faq_question_scan_chars", 180))] and file_role.startswith("secondary"):
        return "qa_or_faq"
    if is_heading(text):
        return "heading"
    if re.match(str(config.get("list_item_regex", r"^(\(?\d+[a-z]?\)|[a-z]\.|[ivxlcdm]+\.)\s+")), text, flags=re.IGNORECASE):
        return "list_item"
    return "paragraph"


def markdown_table_header(block_text: str) -> list[str]:
    rows = markdown_table_rows(block_text)
    if len(rows) < 2:
        return []
    header = rows[0]
    if len(header) < 2:
        return []
    normalized_cells = [normalize_space(cell).lower() for cell in header]
    joined = " ".join(normalized_cells)
    first_cell = normalized_cells[0]
    header_terms = ("dokumen", "persyaratan", "penjelasan", "service", "scenario", "expected", "request")
    term_hits = sum(1 for term in header_terms if term in joined)
    if first_cell in {"no", "no.", "nomor"} and term_hits >= 1:
        return header
    if term_hits >= 3:
        return header
    return []


def table_has_separator_after_header(block_text: str) -> bool:
    lines = [line for line in block_text.splitlines() if "|" in line]
    return len(lines) >= 2 and is_table_separator(lines[1])


def should_apply_table_context(manifest: dict[str, Any]) -> bool:
    suffix = Path(str(manifest.get("resolved_path") or "")).suffix.lower()
    return suffix in {".xlsx", ".docx", ".ods", ".odt"} or manifest.get("file_role") in {"attachment", "operational_requirement"}


def table_context_prefix(header: list[str]) -> str:
    columns = " | ".join(normalize_table_row([cell]) for cell in header if cell)
    return f"Kolom tabel: {columns}."


def enrich_table_block_text(
    block_text: str,
    markdown_text: str,
    manifest: dict[str, Any],
    last_table_header: list[str],
) -> tuple[str, dict[str, Any] | None]:
    if not last_table_header or not should_apply_table_context(manifest):
        return markdown_text, None
    if markdown_table_header(block_text):
        return markdown_text, None
    if not markdown_table_rows(block_text):
        return markdown_text, None
    prefix = table_context_prefix(last_table_header)
    return normalize_space(f"{prefix} {markdown_text}"), {
        "type": "continued_table",
        "columns": last_table_header,
        "source": "previous_table_header",
    }


def raw_output_path(file_id: str) -> Path:
    config = heuristic_section("extraction_heuristics", "raw_output")
    return RAW_LITEPARSE_DIR / f"{slugify(file_id)[: int(config.get('slug_max_chars', 160))]}-{short_hash(file_id)}.json"


def page_to_json(page: Any) -> dict[str, Any]:
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
    empty_pages = sum(1 for page in pages if len(safe_text(page.get("text") or page.get("markdown"))) < int(config.get("empty_page_text_chars", 20)))
    empty_ratio = empty_pages / len(pages)
    if total_text_len < int(config.get("total_text_min_chars", 100)):
        return "likely_needs_ocr", "document_text_under_100_chars"
    if empty_ratio > float(config.get("empty_page_ratio_threshold", 0.70)):
        return "likely_needs_ocr", "more_than_70_percent_pages_empty"
    return "extracted_ok", None


def extract_blocks(manifest: dict[str, Any], pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    heading_config = heuristic_section("extraction_heuristics", "headings")
    block_id_config = heuristic_section("extraction_heuristics", "block_id")
    blocks: list[dict[str, Any]] = []
    current_pasal: str | None = None
    current_ayat: str | None = None
    heading_path: list[str] = []
    last_table_header: list[str] = []

    for page in pages:
        page_num = page.get("page_num")
        page_text = page.get("markdown") or page.get("text") or ""
        for index, block_text in enumerate(sentence_like_blocks(page_text)):
            previous_pasal = current_pasal
            current_pasal = detect_pasal(block_text, current_pasal)
            if current_pasal != previous_pasal:
                current_ayat = None
            detected_ayat = detect_ayat(block_text, current_ayat)
            detected_huruf = detect_huruf(block_text, allow_context_reference=not current_ayat or bool(detected_ayat))

            if is_heading(block_text):
                heading_text = block_text[: int(heading_config.get("heading_text_max_chars", 120))]
                if re.match(str(heading_config.get("bab_heading_regex", r"^BAB\b")), block_text, flags=re.IGNORECASE):
                    heading_path = [heading_text]
                elif len(heading_path) < int(heading_config.get("max_heading_path_items", 4)):
                    heading_path = [*heading_path, heading_text]

            block_type = detect_block_type(block_text, manifest["file_role"])
            if detected_ayat:
                current_ayat = detected_ayat
            if block_type == "table_or_row":
                ayat = detected_ayat
            else:
                ayat = detected_ayat or (current_ayat if detected_huruf else None)
            huruf = detected_huruf
            markdown_text = normalize_extracted_text(block_text, block_type)
            geometry_text = geometry_text_for_block(block_text, page) if block_type == "table_or_row" else None
            table_context = None
            if block_type == "table_or_row":
                header = markdown_table_header(block_text)
                if header and table_has_separator_after_header(block_text):
                    last_table_header = header
                elif header and not last_table_header:
                    last_table_header = header
                markdown_text, table_context = enrich_table_block_text(block_text, markdown_text, manifest, last_table_header)
            normalized_block_text = geometry_text or markdown_text
            block_id_seed = f"{manifest['file_id']}:{page_num}:{index}:{current_pasal or ''}:{ayat or ''}:{huruf or ''}"
            block_id = slugify(block_id_seed)[: int(block_id_config.get("slug_max_chars", 180))]
            blocks.append(
                {
                    "block_id": f"{block_id}-{short_hash(block_id_seed)}",
                    "canonical_id": manifest["canonical_id"],
                    "file_id": manifest["file_id"],
                    "source": manifest["source"],
                    "issuer": manifest["issuer"],
                    "file_role": manifest["file_role"],
                    "document_title": manifest["title"],
                    "regulation_type": manifest["regulation_type"],
                    "number": manifest["number"],
                    "year": manifest["year"],
                    "page_start": page_num,
                    "page_end": page_num,
                    "block_type": block_type,
                    "extraction_method": "geometry_list" if geometry_text else "markdown",
                    "heading_path": heading_path,
                    "pasal": current_pasal,
                    "ayat": ayat,
                    "huruf": huruf,
                    "text": normalized_block_text,
                    "text_markdown": markdown_text,
                    "text_geometry": geometry_text,
                    "table_context": table_context,
                    "citation": {
                        "document": manifest["title"],
                        "page": page_num,
                        "pasal": current_pasal,
                        "ayat": ayat,
                        "huruf": huruf,
                    },
                    "confidence": {
                        "page": "high" if page_num else "missing",
                        "pasal": "medium" if current_pasal else "missing",
                        "ayat": "medium" if ayat else "missing",
                        "huruf": "medium" if huruf else "missing",
                    },
                }
            )

    return blocks
