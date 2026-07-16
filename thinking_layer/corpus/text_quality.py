"""Canonical display-text normalization and publication quality checks.

Raw LiteParse Markdown is preserved as evidence.  This module defines the
separate, stricter contract for text that is allowed into a display, retrieval,
catalog, or context field.
"""

from __future__ import annotations

import re

from markdown_it import MarkdownIt
from markdown_it.token import Token

from ..common.text import normalize_space


_INLINE_PARSER = MarkdownIt("commonmark")
_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\([^)]*\)")
_HEADING = re.compile(r"(?m)^\s{0,3}#{1,6}\s+")
_UNPARSED_EMPHASIS = re.compile(
    r"(?<!\S)(?:\*{1,2}|_{1,2})(?=[A-Za-zÀ-ÖØ-öø-ÿ])"
    r"|(?<=[A-Za-zÀ-ÖØ-öø-ÿ])(?:\*{1,2}|_{1,2})(?=\s|$)"
)
_TRAILING_UNPARSED_EMPHASIS = re.compile(r"(?<=\s)(?:\*{1,2}|_{1,2})$")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_MARKDOWN_PRESENTATION = re.compile(
    r"(?m)^\s{0,3}#{1,6}\s|(?<!\S)(?<!\*)\*\*(?!\*|\))[^*\n]+\*\*(?!\*)"
    r"|(?<!_)__(?!_)[^_\n]+(?<!_)__(?!_)|`[^`\n]+`|\[[^\]]+\]\([^)]*\)"
)
# A title-cased character run has an unambiguous word boundary: ``P e r a t u r a n``
# is one word.  Uppercase-only runs such as ``S U R A T E D A R A N`` are ambiguous
# (they may encode multiple words), so they are rejected rather than guessed at.
_TITLE_CASED_SPACED_WORD = re.compile(r"(?<!\w)([A-Z](?:\s+[a-z]){3,})(?!\w)")
_SPACED_LETTERS = re.compile(r"(?<!\w)(?:[A-Za-z]\s+){3,}[A-Za-z](?!\w)")


class DisplayTextQualityError(ValueError):
    """Text cannot be published without guessing at corrupted source wording."""


def _inline_parts(token: Token) -> list[str]:
    parts: list[str] = []
    for child in token.children or ():
        if child.type in {"text", "code_inline", "html_inline", "image"}:
            parts.append(child.content)
        elif child.type in {"softbreak", "hardbreak"}:
            parts.append("\n")
    return parts


def _markdown_to_text(value: str) -> str:
    parts: list[str] = []
    for token in _INLINE_PARSER.parse(value):
        if token.type == "inline":
            inline = "".join(_inline_parts(token))
            if inline:
                parts.append(inline)
        elif token.type in {"fence", "code_block"} and token.content:
            parts.append(token.content)
    return "\n".join(parts) or value


def _join_unambiguous_spaced_words(value: str) -> str:
    return _TITLE_CASED_SPACED_WORD.sub(
        lambda match: re.sub(r"\s+", "", match.group(1)), value
    )


def clean_display_text(value: str) -> str:
    """Render Markdown to readable text without altering raw provenance."""

    text = _markdown_to_text(value)
    # Balanced inline-code delimiters are consumed by MarkdownIt above.  Any
    # surviving backtick is therefore a source glyph, commonly used in these
    # Indonesian legal documents as an apostrophe in Arabic transliteration;
    # render it as that punctuation rather than allowing separate nodes to
    # accidentally form a Markdown code span when contexts are assembled.
    text = text.replace("`", "'")
    previous = None
    while text != previous:
        previous = text
        text = _HEADING.sub("", text)
    text = _LINK.sub(r"\1", text)
    text = _UNPARSED_EMPHASIS.sub("", text)
    text = _TRAILING_UNPARSED_EMPHASIS.sub("", text)
    text = _join_unambiguous_spaced_words(text)
    return "\n".join(part.strip() for part in text.splitlines()).strip()


def display_text_issue(value: str) -> str | None:
    """Return the first publication-blocking quality defect, if any."""

    if not value.strip():
        return "empty display text"
    if _CONTROL.search(value):
        return "contains non-printing control characters"
    if _MARKDOWN_PRESENTATION.search(value):
        return "contains Markdown presentation syntax"
    if _SPACED_LETTERS.search(value):
        return "contains ambiguous spaced-character text"
    return None


def require_publishable_display_text(value: str) -> str:
    """Normalize then reject text that cannot be safely published as readable text."""

    cleaned = clean_display_text(value)
    # Markdown tables can have syntactic separator or empty structural blocks.
    # They are retained as raw provenance but never become citable/display nodes.
    if not cleaned:
        return cleaned
    if issue := display_text_issue(cleaned):
        raise DisplayTextQualityError(issue)
    return cleaned


def retrieval_text(value: str) -> str:
    return normalize_space(value)
