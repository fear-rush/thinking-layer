from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..common.text import normalize_space
from .normalization import normalize_list_text


ENUMERATOR_PREFIX_RE = re.compile(r"^(\(?\d+[a-z]?\)|[a-z]\.|[ivxlcdm]+\.)\s+(.+)$", flags=re.IGNORECASE)
PAGE_NUMBER_RE = re.compile(r"^-?\d+-?$")
FOOTER_OR_HEADER_RE = re.compile(r"^(https?://|www\.|jdih\.|ojk\.go\.id|bankindonesia\.go\.id)", flags=re.IGNORECASE)


@dataclass(frozen=True)
class GeometryLine:
    text: str
    x: float
    y: float


@dataclass(frozen=True)
class GeometryEntry:
    label: str
    text: str
    first_y: float
    last_y: float


def item_text(item: dict[str, Any]) -> str:
    return normalize_space(str(item.get("text") or ""))


def geometry_lines_from_page(page: dict[str, Any], y_tolerance: float = 3.0) -> list[GeometryLine]:
    items = []
    for item in page.get("text_items") or []:
        text = item_text(item)
        if not text:
            continue
        x = float(item.get("x") or 0.0)
        y = float(item.get("y") or 0.0)
        items.append((y, x, text))
    items.sort(key=lambda value: (value[0], value[1]))

    grouped: list[list[tuple[float, float, str]]] = []
    for item in items:
        if not grouped or abs(grouped[-1][0][0] - item[0]) > y_tolerance:
            grouped.append([item])
        else:
            grouped[-1].append(item)

    lines: list[GeometryLine] = []
    for group in grouped:
        group.sort(key=lambda value: value[1])
        text = normalize_space(" ".join(value[2] for value in group))
        if not text or PAGE_NUMBER_RE.fullmatch(text.strip("- ")) or FOOTER_OR_HEADER_RE.match(text):
            continue
        lines.append(GeometryLine(text=text, x=min(value[1] for value in group), y=sum(value[0] for value in group) / len(group)))
    return lines


def entry_label(text: str) -> str | None:
    match = ENUMERATOR_PREFIX_RE.match(text)
    if not match:
        return None
    return match.group(1).lower()


def reconstruct_indented_entries(page: dict[str, Any]) -> list[GeometryEntry]:
    entries: list[GeometryEntry] = []
    current_label: str | None = None
    current_parts: list[str] = []
    current_content_x: float | None = None
    first_y = 0.0
    last_y = 0.0

    def flush() -> None:
        nonlocal current_label, current_parts, current_content_x, first_y, last_y
        if current_label and current_parts:
            entries.append(
                GeometryEntry(
                    label=current_label,
                    text=normalize_list_text(" ".join(current_parts)),
                    first_y=first_y,
                    last_y=last_y,
                )
            )
        current_label = None
        current_parts = []
        current_content_x = None
        first_y = 0.0
        last_y = 0.0

    for line in geometry_lines_from_page(page):
        label = entry_label(line.text)
        if label:
            flush()
            current_label = label
            current_parts = [line.text]
            current_content_x = line.x
            first_y = line.y
            last_y = line.y
            continue
        if current_label and current_content_x is not None and line.x >= current_content_x + 10:
            current_parts.append(line.text)
            last_y = line.y
            continue
        flush()

    flush()
    return entries


def labels_in_text(text: str) -> list[str]:
    labels = []
    for match in re.finditer(r"(?<!\w)(\(?\d+[a-z]?\)|[a-z]\.|[ivxlcdm]+\.)\s+", text, flags=re.IGNORECASE):
        labels.append(match.group(1).lower())
    return labels


def geometry_text_for_block(block_text: str, page: dict[str, Any]) -> str | None:
    labels = labels_in_text(block_text)
    if not labels:
        return None
    entries = reconstruct_indented_entries(page)
    matched: list[str] = []
    for start_index in range(0, max(0, len(entries) - len(labels) + 1)):
        window = entries[start_index : start_index + len(labels)]
        if [entry.label for entry in window] == labels:
            matched = [entry.text for entry in window]
            break
    if not matched:
        return None
    return normalize_space("; ".join(matched)).strip(" ;")
