from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..domain.legal import LegalNode, LegalPath, SourceSpan
from .eligibility import OcrEligibility
from .liteparse_normalizer import (
    NormalizedBlock,
    NormalizedDocument,
    NormalizedPage,
    normalize_raw_document,
)


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
                self.angka_node_id
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
            self.pasal_node_id = self.ayat_node_id = self.huruf_node_id = (
                self.angka_node_id
            ) = None
            return
        if kind == "pasal":
            self.pasal, self.ayat, self.huruf, self.angka = value, None, None, None
            (
                self.pasal_node_id,
                self.ayat_node_id,
                self.huruf_node_id,
                self.angka_node_id,
            ) = node_id, None, None, None
            return
        if kind == "ayat":
            self.ayat, self.huruf, self.angka = value, None, None
            self.ayat_node_id, self.huruf_node_id, self.angka_node_id = (
                node_id,
                None,
                None,
            )
            return
        if kind == "huruf":
            self.huruf, self.angka = value, None
            self.huruf_node_id, self.angka_node_id = node_id, None
            return
        if kind == "angka":
            self.angka, self.angka_node_id = value, node_id


def _plain_line(line: str) -> str:
    line = line.strip().strip("*_ " + chr(96))
    if match := _MARKDOWN_HEADING.match(line):
        line = match.group(1)
    return " ".join(line.split())


def _anchor(
    line: str, *, allow_subprovision: bool, heading_block: bool
) -> tuple[str, str | None] | None:
    plain = _plain_line(line)
    if not plain:
        return None
    if _STRUCTURAL_HEADING.match(plain):
        return "heading", plain
    if match := _PASAL.match(plain):
        return "pasal", match.group(1)
    if heading_block or not allow_subprovision:
        return None
    if match := _AYAT.match(plain):
        return "ayat", match.group(1)
    if match := _HURUF.match(plain):
        return "huruf", match.group(1).lower()
    if match := _ANGKA.match(plain):
        return "angka", match.group(1)
    return None


def _line_anchors(
    line: str, *, state: _ParseState, heading_block: bool
) -> tuple[tuple[int, tuple[str, str | None]], ...]:
    anchors: list[tuple[int, tuple[str, str | None]]] = []
    leading_offset = len(line) - len(line.lstrip())
    if anchor := _anchor(
        line, allow_subprovision=state.pasal is not None, heading_block=heading_block
    ):
        anchors.append((leading_offset, anchor))
    if state.pasal is not None and not heading_block:
        for match in _INLINE_AYAT.finditer(line):
            value = match.group(1).strip()[1:-1].strip()
            anchors.append((match.start(1), ("ayat", value)))
        for match in _INLINE_HURUF.finditer(line):
            value = match.group(1).strip()[0].lower()
            anchors.append((match.start(1), ("huruf", value)))
    return tuple(sorted(dict(anchors).items()))


def _line_ranges(text: str) -> tuple[tuple[int, int, str], ...]:
    ranges: list[tuple[int, int, str]] = []
    start = 0
    for line in text.splitlines(keepends=True):
        end = start + len(line)
        ranges.append((start, end, line))
        start = end
    if start < len(text):
        ranges.append((start, len(text), text[start:]))
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
    page_markdown: str,
    start: int,
    end: int,
    kind: str,
    path: LegalPath,
    parent_node_id: str | None,
) -> LegalNode | None:
    start, end = _trimmed_range(page_markdown, start, end)
    if start == end:
        return None
    text = page_markdown[start:end]
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


def _content_range(block: NormalizedBlock) -> tuple[int, int]:
    """Exclude Markdown fence syntax while retaining the exact text it wraps."""

    start = block.source_range.char_start
    end = block.source_range.char_end
    if block.kind != "verbatim_block":
        return start, end
    lines = _line_ranges(block.raw_markdown)
    if lines and lines[0][2].lstrip().startswith(("```", "~~~")):
        start += lines[0][1]
    if lines and lines[-1][2].lstrip().startswith(("```", "~~~")):
        end = block.source_range.char_start + lines[-1][0]
    return start, end


def _parse_block(
    *, file_id: str, page: NormalizedPage, block: NormalizedBlock, state: _ParseState
) -> list[LegalNode]:
    nodes: list[LegalNode] = []
    content_start, content_end = _content_range(block)
    content_markdown = page.raw_markdown[content_start:content_end]
    active_start = content_start
    active_kind = "continuation" if state.parent_id("continuation") else "preamble"
    active_path = state.legal_path()
    active_parent = state.parent_id(active_kind)

    def flush(end: int) -> None:
        node = _new_node(
            file_id=file_id,
            page_num=page.page_num,
            page_markdown=page.raw_markdown,
            start=active_start,
            end=end,
            kind=active_kind,
            path=active_path,
            parent_node_id=active_parent,
        )
        if node is not None:
            nodes.append(node)
            state.last_node_id = node.node_id

    for line_start, line_end, line in _line_ranges(content_markdown):
        for offset, anchor in _line_anchors(
            line, state=state, heading_block=block.kind == "heading"
        ):
            start = content_start + line_start + offset
            flush(start)
            kind, value = anchor
            node_start, _ = _trimmed_range(
                page.raw_markdown, start, content_start + line_end
            )
            node_id = _node_id(file_id, page.page_num, node_start, kind)
            parent = state.parent_id(kind)
            state.apply_anchor(kind, value, node_id)
            active_start = start
            active_kind = kind
            active_path = state.legal_path()
            active_parent = parent
    flush(content_end)
    return nodes


def parse_normalized_document(normalized: NormalizedDocument) -> ParsedDocument:
    """Derive legal nodes from normalized Markdown blocks, never page-wide strings."""

    state = _ParseState()
    nodes: list[LegalNode] = []
    for page in normalized.pages:
        parseable_blocks = (
            block
            for block in page.blocks
            if block.kind in {"heading", "paragraph", "verbatim_block"}
        )
        for block in parseable_blocks:
            nodes.extend(
                _parse_block(
                    file_id=normalized.file_id, page=page, block=block, state=state
                )
            )
    if not nodes:
        raise ValueError(
            f"fresh raw document {normalized.file_id} produced no legal nodes"
        )
    return ParsedDocument(
        file_id=normalized.file_id, nodes=tuple(nodes), page_count=len(normalized.pages)
    )


def parse_raw_document(raw_record: Mapping[str, Any]) -> ParsedDocument:
    return parse_normalized_document(normalize_raw_document(raw_record))


def parse_saved_raw(path: Path, eligibility: OcrEligibility) -> ParsedDocument | None:
    """Load one fresh raw extraction, enforcing OCR exclusion before parsing."""

    try:
        raw_record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid fresh raw JSON: {path}") from error
    if not isinstance(raw_record, Mapping):
        raise ValueError(f"fresh raw JSON must be an object: {path}")
    file_id = raw_record.get("file_id")
    if not isinstance(file_id, str) or not file_id.strip():
        raise ValueError(f"fresh raw document requires file_id: {path}")
    if not eligibility.is_eligible(file_id):
        return None
    eligibility.validate_raw_record(raw_record)
    return parse_raw_document(raw_record)
