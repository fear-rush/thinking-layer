"""Lossless normalization of fresh LiteParse Markdown.

The fresh raw record remains extraction evidence; the downloaded source document
remains authoritative. This module derives a typed block tree whose ranges point
back into the unmodified page Markdown.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from itertools import pairwise
from math import ceil
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.token import Token

from ..common.text import normalize_space


_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^\s)]+)(?:\s+[^)]*)?\)")
_TABLE_DELIMITER = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(?:\|\s*:?-{1,}:?\s*)+\|?\s*$")
_WORD = re.compile(r"[\wÀ-ÖØ-öø-ÿ]+", re.UNICODE)
_FRESH_CONTRACT = "thinking-layer-fresh-liteparse-v1"
_GEOMETRY_BLOCK_KINDS = {
    "heading",
    "paragraph",
    "list_item",
    "table_header_cell",
    "table_cell",
    "verbatim_block",
}


class MarkdownNormalizationError(ValueError):
    """A source construct that cannot become an exactly anchored block."""

    def __init__(self, file_id: str, page_num: int, reason: str) -> None:
        super().__init__(f"{file_id}, page {page_num}: {reason}")
        self.file_id = file_id
        self.page_num = page_num
        self.reason = reason


@dataclass(frozen=True)
class MarkdownRange:
    """An exact half-open character range in a single saved Markdown page."""

    page_num: int
    line_start: int
    line_end: int
    char_start: int
    char_end: int

    def __post_init__(self) -> None:
        if self.page_num < 1:
            raise ValueError("Markdown range page_num must be positive")
        if self.line_start < 0 or self.line_end < self.line_start:
            raise ValueError("Markdown range lines must be ordered")
        if self.char_start < 0 or self.char_end < self.char_start:
            raise ValueError("Markdown range characters must be ordered")


@dataclass(frozen=True)
class MarkdownLink:
    text: str
    target: str
    source_range: MarkdownRange


@dataclass(frozen=True)
class GeometryAnchor:
    """A page-region confirmation for a Markdown-derived block."""

    page_num: int
    x: float
    y: float
    width: float
    height: float
    text_item_count: int


@dataclass(frozen=True)
class GeometryDisagreement:
    block_id: str
    page_num: int
    reason: str


@dataclass(frozen=True)
class NormalizedBlock:
    """A Markdown-derived semantic block with lossless provenance."""

    block_id: str
    kind: str
    source_range: MarkdownRange
    raw_markdown: str
    display_text: str
    retrieval_text: str
    parent_block_id: str | None
    child_block_ids: tuple[str, ...]
    links: tuple[MarkdownLink, ...] = ()
    zone: str = "unknown"
    geometry_anchor: GeometryAnchor | None = None
    quarantine_reason: str | None = None


@dataclass(frozen=True)
class NormalizedPage:
    page_num: int
    raw_markdown: str
    blocks: tuple[NormalizedBlock, ...]

    def block(self, block_id: str) -> NormalizedBlock:
        for block in self.blocks:
            if block.block_id == block_id:
                return block
        raise KeyError(block_id)


@dataclass(frozen=True)
class NormalizedDocument:
    file_id: str
    pages: tuple[NormalizedPage, ...]
    family: str = "other"
    geometry_disagreements: tuple[GeometryDisagreement, ...] = ()


@dataclass
class _BlockDraft:
    kind: str
    parent_index: int | None
    source_range: MarkdownRange | None
    display_text: str = ""


_OPENING_KINDS = {
    "heading_open": "heading",
    "paragraph_open": "paragraph",
    "ordered_list_open": "ordered_list",
    "bullet_list_open": "bullet_list",
    "list_item_open": "list_item",
    "table_open": "table",
    "thead_open": "table_head",
    "tbody_open": "table_body",
    "tr_open": "table_row",
    "th_open": "table_header_cell",
    "td_open": "table_cell",
    "hr": "thematic_break",
    "fence": "verbatim_block",
    "code_block": "verbatim_block",
}


def _line_offsets(markdown: str) -> tuple[int, ...]:
    offsets = [0]
    for index, character in enumerate(markdown):
        if character == "\n":
            offsets.append(index + 1)
    return tuple(offsets)


def _range_from_map(
    *,
    page_num: int,
    offsets: tuple[int, ...],
    markdown_length: int,
    token_map: list[int] | None,
) -> MarkdownRange | None:
    if token_map is None:
        return None
    if len(token_map) != 2:
        raise ValueError(
            f"Markdown token source map must contain two lines: {token_map!r}"
        )
    line_start, line_end = token_map
    if line_start < 0 or line_end < line_start or line_start >= len(offsets):
        raise ValueError(
            f"Markdown token source map is outside the page: {token_map!r}"
        )
    char_start = offsets[line_start]
    char_end = offsets[line_end] if line_end < len(offsets) else markdown_length
    return MarkdownRange(page_num, line_start, line_end, char_start, char_end)


def _inline_text(token: Token) -> str:
    children = token.children or ()
    parts: list[str] = []
    for child in children:
        if child.type in {"text", "code_inline", "html_inline", "image"}:
            parts.append(child.content)
        elif child.type in {"softbreak", "hardbreak"}:
            parts.append("\n")
    return "".join(parts) or token.content


def _table_cells(line: str) -> tuple[tuple[int, int], ...]:
    """Return exact cell slices for a single GFM table row.

    Escaped pipes are part of a cell, so they do not split it.
    """

    content_end = len(line.rstrip("\r\n"))
    if not line[:content_end].strip():
        return ()
    boundaries = [-1]
    escaped = False
    for index, character in enumerate(line[:content_end]):
        if character == "|" and not escaped:
            boundaries.append(index)
        escaped = character == "\\" and not escaped
        if character != "\\":
            escaped = False
    boundaries.append(content_end)
    if len(boundaries) < 3:
        return ()
    if boundaries[1] != 0:
        boundaries.insert(1, 0)
    if boundaries[-2] != content_end - 1:
        boundaries.insert(-1, content_end)
    cells: list[tuple[int, int]] = []
    for start, end in pairwise(boundaries):
        if start == -1 or end == content_end:
            continue
        cell_start = start + 1
        while cell_start < end and line[cell_start].isspace():
            cell_start += 1
        cell_end = end
        while cell_end > cell_start and line[cell_end - 1].isspace():
            cell_end -= 1
        cells.append((cell_start, cell_end))
    return tuple(cells)


def _assign_table_cell_ranges(
    drafts: list[_BlockDraft],
    markdown: str,
    offsets: tuple[int, ...],
    file_id: str,
    page_num: int,
) -> None:
    for row_index, row in enumerate(drafts):
        if row.kind != "table_row" or row.source_range is None:
            continue
        cell_indexes = [
            index
            for index, draft in enumerate(drafts)
            if draft.parent_index == row_index and "cell" in draft.kind
        ]
        if not cell_indexes:
            continue
        line_start = offsets[row.source_range.line_start]
        line_end = (
            offsets[row.source_range.line_end]
            if row.source_range.line_end < len(offsets)
            else len(markdown)
        )
        line = markdown[line_start:line_end]
        if _TABLE_DELIMITER.match(line.rstrip("\r\n")):
            continue
        cell_ranges = _table_cells(line)
        if len(cell_ranges) != len(cell_indexes):
            raise MarkdownNormalizationError(
                file_id,
                page_num,
                "table row could not be mapped to its parsed cells "
                f"at lines {row.source_range.line_start}:{row.source_range.line_end}",
            )
        for cell_index, (start, end) in zip(cell_indexes, cell_ranges, strict=True):
            drafts[cell_index].source_range = MarkdownRange(
                page_num=page_num,
                line_start=row.source_range.line_start,
                line_end=row.source_range.line_end,
                char_start=line_start + start,
                char_end=line_start + end,
            )


def _links(raw_markdown: str, source_range: MarkdownRange) -> tuple[MarkdownLink, ...]:
    links: list[MarkdownLink] = []
    for match in _LINK.finditer(raw_markdown):
        links.append(
            MarkdownLink(
                text=match.group(1),
                target=match.group(2),
                source_range=MarkdownRange(
                    page_num=source_range.page_num,
                    line_start=source_range.line_start,
                    line_end=source_range.line_end,
                    char_start=source_range.char_start + match.start(),
                    char_end=source_range.char_start + match.end(),
                ),
            )
        )
    return tuple(links)


def normalize_page(*, file_id: str, page_num: int, markdown: str) -> NormalizedPage:
    """Parse one raw LiteParse Markdown page into a deterministic block tree."""

    offsets = _line_offsets(markdown)
    tokens = MarkdownIt("commonmark").enable("table").parse(markdown)
    drafts: list[_BlockDraft] = []
    open_blocks: list[int] = []

    for token in tokens:
        kind = _OPENING_KINDS.get(token.type)
        if kind is not None:
            source_range = _range_from_map(
                page_num=page_num,
                offsets=offsets,
                markdown_length=len(markdown),
                token_map=token.map,
            )
            parent_index = open_blocks[-1] if open_blocks else None
            drafts.append(_BlockDraft(kind, parent_index, source_range))
            if token.nesting == 1:
                open_blocks.append(len(drafts) - 1)
            continue

        if token.type == "inline" and open_blocks:
            drafts[open_blocks[-1]].display_text = _inline_text(token)
            continue

        if token.nesting == -1 and open_blocks:
            open_blocks.pop()

    if open_blocks:
        raise ValueError(f"unbalanced Markdown token stream on page {page_num}")
    _assign_table_cell_ranges(drafts, markdown, offsets, file_id, page_num)

    children_by_parent: dict[int, list[int]] = {
        index: [] for index in range(len(drafts))
    }
    for index, draft in enumerate(drafts):
        if draft.parent_index is not None:
            children_by_parent[draft.parent_index].append(index)

    for index in reversed(range(len(drafts))):
        draft = drafts[index]
        if draft.display_text or draft.source_range is None:
            continue
        child_text = [
            drafts[child].display_text
            for child in children_by_parent[index]
            if drafts[child].display_text
        ]
        if child_text:
            draft.display_text = "\n".join(child_text)
        else:
            draft.display_text = markdown[
                draft.source_range.char_start : draft.source_range.char_end
            ]

    blocks: list[NormalizedBlock] = []
    for index, draft in enumerate(drafts):
        if draft.source_range is None:
            raise MarkdownNormalizationError(
                file_id,
                page_num,
                f"normalized {draft.kind} block has no exact source range",
            )
        block_id = f"{file_id}:page:{page_num}:block:{index}"
        raw_markdown = markdown[
            draft.source_range.char_start : draft.source_range.char_end
        ]
        blocks.append(
            NormalizedBlock(
                block_id=block_id,
                kind=draft.kind,
                source_range=draft.source_range,
                raw_markdown=raw_markdown,
                display_text=draft.display_text,
                retrieval_text=normalize_space(draft.display_text),
                parent_block_id=(
                    f"{file_id}:page:{page_num}:block:{draft.parent_index}"
                    if draft.parent_index is not None
                    else None
                ),
                child_block_ids=tuple(
                    f"{file_id}:page:{page_num}:block:{child}"
                    for child in children_by_parent[index]
                ),
                links=_links(raw_markdown, draft.source_range),
            )
        )
    return NormalizedPage(
        page_num=page_num, raw_markdown=markdown, blocks=tuple(blocks)
    )


def _page_markdown(page: Mapping[str, Any]) -> str:
    markdown = page.get("markdown")
    if isinstance(markdown, str) and markdown.strip():
        return markdown
    text = page.get("text")
    if isinstance(text, str) and text.strip():
        return text
    raise ValueError("fresh raw page requires non-empty markdown or text")


def _document_family(
    raw_record: Mapping[str, Any], pages: tuple[NormalizedPage, ...]
) -> str:
    """Classify only from saved source evidence; never infer a legal zone by number."""

    source_hint = " ".join(
        str(raw_record.get(key) or "")
        for key in ("file_id", "source_path", "source_url")
    ).casefold()
    markdown_hint = "\n".join(page.raw_markdown for page in pages[:2]).casefold()
    evidence = f"{source_hint}\n{markdown_hint}"
    if "faq" in evidence or "frequently asked" in evidence:
        return "faq"
    if "penjelasan" in source_hint or markdown_hint.lstrip().startswith("penjelasan"):
        return "explanation"
    if "lampiran" in source_hint or markdown_hint.lstrip().startswith("lampiran"):
        return "attachment"
    if "surat edaran" in evidence or "seojk" in evidence or "sebi" in evidence:
        return "circular"
    if "keputusan" in evidence or re.search(r"\bsk\b", source_hint):
        return "decision"
    if "peraturan" in evidence or re.search(
        r"(?m)^pasal\s+\d+", markdown_hint, flags=re.IGNORECASE
    ):
        return "regulation"
    return "other"


def _zoned_pages(
    pages: tuple[NormalizedPage, ...], *, family: str
) -> tuple[NormalizedPage, ...]:
    """Mark source-backed document zones before legal-anchor interpretation."""

    default_zone = "normative" if family in {"regulation", "decision"} else family
    zone = default_zone
    zoned_pages: list[NormalizedPage] = []
    for page in pages:
        zoned_blocks: list[NormalizedBlock] = []
        for block in page.blocks:
            marker = normalize_space(
                block.display_text or block.raw_markdown
            ).casefold()
            if family in {"regulation", "decision"}:
                if marker.startswith("penjelasan"):
                    zone = "explanation"
                elif marker.startswith("lampiran"):
                    zone = "attachment"
            zoned_blocks.append(replace(block, zone=zone))
        zoned_pages.append(replace(page, blocks=tuple(zoned_blocks)))
    return tuple(zoned_pages)


def _tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in _WORD.findall(value)
        if any(character.isalpha() for character in token) and len(token) >= 2
    }


def _geometry_items(
    page: Mapping[str, Any],
) -> tuple[tuple[str, float, float, float, float], ...]:
    raw_items = page.get("text_items")
    if not isinstance(raw_items, list):
        return ()
    items: list[tuple[str, float, float, float, float]] = []
    for item in raw_items:
        if not isinstance(item, Mapping):
            continue
        text = item.get("text")
        coordinates = tuple(item.get(name) for name in ("x", "y", "width", "height"))
        if not isinstance(text, str) or not text.strip():
            continue
        if not all(isinstance(value, (int, float)) for value in coordinates):
            continue
        x, y, width, height = (float(value) for value in coordinates)
        if width <= 0 or height <= 0:
            continue
        items.append((text, x, y, width, height))
    return tuple(items)


def _geometry_validated_page(
    page: NormalizedPage, raw_page: Mapping[str, Any], *, enforce: bool
) -> tuple[NormalizedPage, tuple[GeometryDisagreement, ...]]:
    if not enforce:
        return page, ()
    items = _geometry_items(raw_page)
    disagreements: list[GeometryDisagreement] = []
    blocks: list[NormalizedBlock] = []
    for block in page.blocks:
        if block.kind not in _GEOMETRY_BLOCK_KINDS:
            blocks.append(block)
            continue
        block_tokens = _tokens(block.display_text)
        if not block_tokens:
            blocks.append(block)
            continue
        matching_items = [item for item in items if _tokens(item[0]) & block_tokens]
        matched_tokens = {
            token for item in matching_items for token in _tokens(item[0])
        }
        required_matches = max(1, ceil(len(block_tokens) * 0.5))
        if len(matched_tokens & block_tokens) < required_matches:
            reason = (
                "missing_usable_text_item_geometry"
                if not items
                else "markdown_geometry_text_disagreement"
            )
            disagreements.append(
                GeometryDisagreement(block.block_id, page.page_num, reason)
            )
            blocks.append(replace(block, quarantine_reason=reason))
            continue
        x_start = min(item[1] for item in matching_items)
        y_start = min(item[2] for item in matching_items)
        x_end = max(item[1] + item[3] for item in matching_items)
        y_end = max(item[2] + item[4] for item in matching_items)
        blocks.append(
            replace(
                block,
                geometry_anchor=GeometryAnchor(
                    page_num=page.page_num,
                    x=x_start,
                    y=y_start,
                    width=x_end - x_start,
                    height=y_end - y_start,
                    text_item_count=len(matching_items),
                ),
            )
        )
    return replace(page, blocks=tuple(blocks)), tuple(disagreements)


def normalize_raw_document(raw_record: Mapping[str, Any]) -> NormalizedDocument:
    """Normalize a saved non-OCR LiteParse record without modifying its source text."""

    file_id = raw_record.get("file_id")
    if not isinstance(file_id, str) or not file_id.strip():
        raise ValueError("fresh raw document requires file_id")
    pages = raw_record.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError(f"fresh raw document {file_id} requires pages")
    normalized_pages: list[NormalizedPage] = []
    raw_pages: list[Mapping[str, Any]] = []
    seen_pages: set[int] = set()
    for page in pages:
        if not isinstance(page, Mapping):
            raise ValueError(f"fresh raw document {file_id} contains an invalid page")
        page_num = page.get("page_num")
        if not isinstance(page_num, int) or page_num < 1:
            raise ValueError(f"fresh raw document {file_id} has an invalid page_num")
        if page_num in seen_pages:
            raise ValueError(
                f"fresh raw document {file_id} has duplicate page_num {page_num}"
            )
        seen_pages.add(page_num)
        raw_pages.append(page)
        normalized_pages.append(
            normalize_page(
                file_id=file_id, page_num=page_num, markdown=_page_markdown(page)
            )
        )
    pages = tuple(normalized_pages)
    family = _document_family(raw_record, pages)
    zoned_pages = _zoned_pages(pages, family=family)
    enforce_geometry = raw_record.get("contract") == _FRESH_CONTRACT
    geometry_disagreements: list[GeometryDisagreement] = []
    validated_pages: list[NormalizedPage] = []
    for page, raw_page in zip(zoned_pages, raw_pages, strict=True):
        validated_page, disagreements = _geometry_validated_page(
            page, raw_page, enforce=enforce_geometry
        )
        validated_pages.append(validated_page)
        geometry_disagreements.extend(disagreements)
    return NormalizedDocument(
        file_id=file_id,
        pages=tuple(validated_pages),
        family=family,
        geometry_disagreements=tuple(geometry_disagreements),
    )
