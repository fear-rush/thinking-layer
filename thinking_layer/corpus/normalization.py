from __future__ import annotations

import re

from ..common.text import normalize_space


ENUMERATOR_RE = re.compile(r"^(\(?\d+[a-z]?\)|[a-z]\.|[ivxlcdm]+\.)$", flags=re.IGNORECASE)
MARKDOWN_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")


def clean_cell(value: str) -> str:
    value = normalize_space(value)
    value = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", value)
    value = value.strip(" \t\r\n|")
    value = normalize_space(value)
    return value.strip(" ;")


def is_separator_cell(value: str) -> bool:
    return bool(MARKDOWN_SEPARATOR_RE.fullmatch(clean_cell(value)))


def row_cells_from_line(line: str) -> list[str]:
    cells = [clean_cell(cell) for cell in line.strip().strip("|").split("|")]
    return [cell for cell in cells if cell]


def flattened_pipe_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    current: list[str] = []
    for raw_cell in text.split("|"):
        cell = clean_cell(raw_cell)
        if not cell:
            if current:
                rows.append(current)
                current = []
            continue
        current.append(cell)
    if current:
        rows.append(current)
    return rows


def markdown_table_rows(text: str) -> list[list[str]]:
    if "|" not in text:
        return []
    if "\n" not in text:
        rows = flattened_pipe_rows(text)
    else:
        rows = [row_cells_from_line(line) for line in text.splitlines() if "|" in line]
    return [
        row
        for row in rows
        if row and not all(is_separator_cell(cell) for cell in row)
    ]


def normalize_table_row(cells: list[str]) -> str:
    cells = [cell for cell in cells if cell and not is_separator_cell(cell)]
    if not cells:
        return ""
    if len(cells) >= 2 and ENUMERATOR_RE.fullmatch(cells[0]):
        return normalize_space(f"{cells[0]} {' '.join(cells[1:])}").strip(" ;")
    return normalize_space(" - ".join(cells)).strip(" ;")


def normalize_markdown_table_text(text: str) -> str:
    rows = [normalize_table_row(row) for row in markdown_table_rows(text)]
    rows = [row for row in rows if row]
    if not rows:
        return normalize_space(text)
    return normalize_space("; ".join(rows)).strip(" ;")


def normalize_list_text(text: str) -> str:
    value = normalize_space(text)
    value = re.sub(r"\s+([,.;:])", r"\1", value)
    value = re.sub(r"([a-z])\.;\s+", r"\1. ", value, flags=re.IGNORECASE)
    value = re.sub(r"\b([a-z])\.\s*;\s*", r"\1. ", value, flags=re.IGNORECASE)
    value = re.sub(r":\s*;", ":", value)
    value = re.sub(r";\s+(dan|atau);", r"; \1", value, flags=re.IGNORECASE)
    value = re.sub(r";\s*;", ";", value)
    return normalize_space(value).strip(" ;")


def normalize_extracted_text(text: str, block_type: str | None = None) -> str:
    if block_type == "table_or_row" or "|" in text:
        return normalize_list_text(normalize_markdown_table_text(text))
    return normalize_list_text(text)
