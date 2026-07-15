from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..domain.legal import LegalNode, LegalPath, SourceSpan
from .eligibility import OcrEligibility


_MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+(.+)$")
_STRUCTURAL_HEADING = re.compile(r"^(BAB|BAGIAN|PARAGRAF)\b", re.IGNORECASE)
_PASAL = re.compile(r"^Pasal\s+(\d+[A-Za-z]?)\b", re.IGNORECASE)
_AYAT = re.compile(r"^(?:Ayat\s*)?\(\s*(\d+[A-Za-z]?)\s*\)")
_HURUF = re.compile(r"^(?:Huruf\s+)?([a-z])\s*[.)]\s+", re.IGNORECASE)
_ANGKA = re.compile(r"^(?:Angka\s+)?(\d+)\s*[.)]\s+")
_INLINE_AYAT = re.compile(r"(?<=[.;:])\s+(\(\s*\d+[A-Za-z]?\s*\))")
_INLINE_HURUF = re.compile(r"(?<=[;:])\s+([a-z]\s*[.)])\s+", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedDocument:
    file_id: str
    nodes: tuple[LegalNode, ...]
    page_count: int


@dataclass
class _ParseState:
    heading: tuple[str, ...] = ()
    pasal: str | None = None
    ayat: str | None = None
    huruf: str | None = None
    angka: str | None = None
    pasal_node_id: str | None = None
    ayat_node_id: str | None = None
    huruf_node_id: str | None = None
    angka_node_id: str | None = None
    last_node_id: str | None = None

    def legal_path(self) -> LegalPath:
        return LegalPath(
            pasal=self.pasal,
            ayat=self.ayat,
            huruf=self.huruf,
            angka=self.angka,
            heading=self.heading,
        )

    def parent_id(self, kind: str) -> str | None:
        if kind == "ayat":
            return self.pasal_node_id
        if kind == "huruf":
            return self.ayat_node_id or self.pasal_node_id
        if kind == "angka":
            return self.huruf_node_id or self.ayat_node_id or self.pasal_node_id
        if kind == "continuation":
            return (
                self.last_node_id
                or self.angka_node_id
                or self.huruf_node_id
                or self.ayat_node_id
                or self.pasal_node_id
            )
        return None

    def apply_anchor(self, kind: str, value: str | None, node_id: str) -> None:
        if kind == "heading":
            assert value is not None
            self.heading = (*self.heading, value)
            self.pasal = self.ayat = self.huruf = self.angka = None
            self.pasal_node_id = self.ayat_node_id = self.huruf_node_id = self.angka_node_id = None
            return
        if kind == "pasal":
            self.pasal, self.ayat, self.huruf, self.angka = value, None, None, None
            self.pasal_node_id, self.ayat_node_id, self.huruf_node_id, self.angka_node_id = (
                node_id,
                None,
                None,
                None,
            )
            return
        if kind == "ayat":
            self.ayat, self.huruf, self.angka = value, None, None
            self.ayat_node_id, self.huruf_node_id, self.angka_node_id = node_id, None, None
            return
        if kind == "huruf":
            self.huruf, self.angka = value, None
            self.huruf_node_id, self.angka_node_id = node_id, None
            return
        if kind == "angka":
            self.angka, self.angka_node_id = value, node_id


def _plain_line(line: str) -> str:
    line = line.strip()
    line = line.strip("*_ " + chr(96))
    match = _MARKDOWN_HEADING.match(line)
    if match:
        line = match.group(1)
    return " ".join(line.split())


def _anchor(line: str) -> tuple[str, str | None] | None:
    plain = _plain_line(line)
    if not plain:
        return None
    if _STRUCTURAL_HEADING.match(plain):
        return "heading", plain
    if match := _PASAL.match(plain):
        return "pasal", match.group(1)
    if match := _AYAT.match(plain):
        return "ayat", match.group(1)
    if match := _HURUF.match(plain):
        return "huruf", match.group(1).lower()
    if match := _ANGKA.match(plain):
        return "angka", match.group(1)
    return None


def _line_anchors(line: str) -> tuple[tuple[int, tuple[str, str | None]], ...]:
    anchors: list[tuple[int, tuple[str, str | None]]] = []
    leading_offset = len(line) - len(line.lstrip())
    if anchor := _anchor(line):
        anchors.append((leading_offset, anchor))
    for match in _INLINE_AYAT.finditer(line):
        value = match.group(1).strip()[1:-1].strip()
        anchors.append((match.start(1), ("ayat", value)))
    for match in _INLINE_HURUF.finditer(line):
        value = match.group(1).strip()[0].lower()
        anchors.append((match.start(1), ("huruf", value)))
    return tuple(sorted(dict(anchors).items()))


def _line_ranges(page_text: str) -> tuple[tuple[int, int, str], ...]:
    ranges: list[tuple[int, int, str]] = []
    start = 0
    for line in page_text.splitlines(keepends=True):
        end = start + len(line)
        ranges.append((start, end, line))
        start = end
    return tuple(ranges)


def _trimmed_range(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _node_id(file_id: str, page_num: int, char_start: int, kind: str) -> str:
    return f"{file_id}:page:{page_num}:char:{char_start}:{kind}"


def _new_node(
    *,
    file_id: str,
    page_num: int,
    page_text: str,
    start: int,
    end: int,
    kind: str,
    path: LegalPath,
    parent_node_id: str | None,
) -> LegalNode | None:
    start, end = _trimmed_range(page_text, start, end)
    if start == end:
        return None
    text = page_text[start:end]
    return LegalNode(
        node_id=_node_id(file_id, page_num, start, kind),
        document_id=file_id,
        node_kind=kind,
        text=text,
        retrieval_text=" ".join(text.split()),
        legal_path=path,
        spans=(SourceSpan(page_num, page_num, start, end),),
        parent_node_id=parent_node_id,
    )


def _page_text(page: Mapping[str, Any]) -> str:
    markdown = page.get("markdown")
    text = markdown if isinstance(markdown, str) and markdown.strip() else page.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("saved raw page requires non-empty markdown or text")
    return text


def _parse_page(
    *,
    file_id: str,
    page_num: int,
    page_text: str,
    state: _ParseState,
) -> list[LegalNode]:
    nodes: list[LegalNode] = []
    active_start = 0
    active_kind = "continuation" if state.parent_id("continuation") else "preamble"
    active_path = state.legal_path()
    active_parent = state.parent_id(active_kind)

    def flush(end: int) -> None:
        node = _new_node(
            file_id=file_id,
            page_num=page_num,
            page_text=page_text,
            start=active_start,
            end=end,
            kind=active_kind,
            path=active_path,
            parent_node_id=active_parent,
        )
        if node is not None:
            nodes.append(node)
            state.last_node_id = node.node_id

    for line_start, line_end, line in _line_ranges(page_text):
        for offset, anchor in _line_anchors(line):
            start = line_start + offset
            flush(start)
            kind, value = anchor
            node_start, _ = _trimmed_range(page_text, start, line_end)
            node_id = _node_id(file_id, page_num, node_start, kind)
            parent = state.parent_id(kind)
            state.apply_anchor(kind, value, node_id)
            active_start = start
            active_kind = kind
            active_path = state.legal_path()
            active_parent = parent
    flush(len(page_text))
    return nodes


def parse_raw_document(raw_record: Mapping[str, Any]) -> ParsedDocument:
    """Parse saved non-OCR LiteParse pages into hierarchy-aware citation nodes."""
    file_id = raw_record.get("file_id")
    if not isinstance(file_id, str) or not file_id.strip():
        raise ValueError("saved raw document requires file_id")
    pages = raw_record.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError(f"saved raw document {file_id} requires pages")

    state = _ParseState()
    nodes: list[LegalNode] = []
    seen_pages: set[int] = set()
    for page in pages:
        if not isinstance(page, Mapping):
            raise ValueError(f"saved raw document {file_id} contains an invalid page")
        page_num = page.get("page_num")
        if not isinstance(page_num, int) or page_num < 1:
            raise ValueError(f"saved raw document {file_id} has an invalid page_num")
        if page_num in seen_pages:
            raise ValueError(f"saved raw document {file_id} has duplicate page_num {page_num}")
        seen_pages.add(page_num)
        nodes.extend(
            _parse_page(
                file_id=file_id,
                page_num=page_num,
                page_text=_page_text(page),
                state=state,
            )
        )
    if not nodes:
        raise ValueError(f"saved raw document {file_id} produced no legal nodes")
    return ParsedDocument(file_id=file_id, nodes=tuple(nodes), page_count=len(pages))


def parse_saved_raw(path: Path, eligibility: OcrEligibility) -> ParsedDocument | None:
    """Load one saved raw extraction, enforcing OCR exclusion before parsing."""
    try:
        raw_record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid saved raw JSON: {path}") from error
    if not isinstance(raw_record, Mapping):
        raise ValueError(f"saved raw JSON must be an object: {path}")
    file_id = raw_record.get("file_id")
    if not isinstance(file_id, str) or not file_id.strip():
        raise ValueError(f"saved raw document requires file_id: {path}")
    if not eligibility.is_eligible(file_id):
        return None
    eligibility.validate_raw_record(raw_record)
    return parse_raw_document(raw_record)
