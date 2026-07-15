"""Parse ordered page text into citation-safe legal structural units.

The existing extraction pipeline is deliberately permissive: it creates small
search blocks from whatever a document parser returned.  This module is the
stricter, lossless layer that sits before v2 chunk selection.  It only depends
on supplied page dictionaries, so fixture tests can exercise legal structure
without LiteParse, generated corpus assets, or a database.

Legal text is hierarchical rather than sentence-shaped.  In particular, an
Ayat or Huruf can continue on a following page without being a new provision.
The parser therefore keeps a single unit open across pages and records its
source spans, instead of manufacturing an orphan continuation chunk.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import re
from typing import Any, Iterable

from ..common.text import normalize_space, slugify
from .metadata import short_hash


CHUNK_SCHEMA_VERSION = 2
MAX_PARENT_LEAD_IN_CHARS = 360
MAX_RETRIEVAL_ALIASES_PER_UNIT = 3
MAX_RETRIEVAL_ALIAS_CHARS = 300
MIN_ENUMERATION_CHILDREN = 2
MAX_ENUMERATION_CHILDREN = 12
MAX_ENUMERATION_AGGREGATE_CHARS = 2_400

_BAB_RE = re.compile(r"^BAB\s+([IVXLCDM]+|\d+)\b(?:\s+(.*))?$", re.IGNORECASE)
_BAGIAN_RE = re.compile(r"^Bagian\s+(.+)$", re.IGNORECASE)
_PARAGRAF_RE = re.compile(r"^Paragraf\s+(.+)$", re.IGNORECASE)
_PASAL_RE = re.compile(r"^Pasal\s+(\d+[A-Z]?)\b(?:\s*(.*))?$", re.IGNORECASE)
_BARE_PASAL_RE = re.compile(r"^Pasal$", re.IGNORECASE)
_AYAT_RE = re.compile(r"^(?:Ayat\s*)?\((\d+[a-z]?)\)\s*(.*)$", re.IGNORECASE)
_HURUF_WORD_RE = re.compile(r"^Huruf\s+([a-z])\b\s*(.*)$", re.IGNORECASE)
_HURUF_RE = re.compile(r"^\(?([a-z])\)?[.)]\s+(.+)$")
_ANGKA_RE = re.compile(r"^\(?([0-9]+)\)?[.)]\s+(.+)$")
_OUTLINE_ROMAN_SECTION_RE = re.compile(r"^([IVXLCDM]+)\.\s+(.+)$")
_OUTLINE_ATTACHMENT_SECTION_RE = re.compile(r"^([A-Z])\.\s+(.+)$")
_OUTLINE_POINT_RE = re.compile(r"^(\d+)\.\s+(.+)$")
_OUTLINE_SUBPOINT_RE = re.compile(r"^([a-z])\.\s+(.+)$")
_OUTLINE_ITEM_RE = re.compile(r"^(\d+)\)\s+(.+)$")
_OUTLINE_INDEX_RE = re.compile(r"(?m)^\s*DAFTAR\s+(?:ISI|GAMBAR)\s*$", re.IGNORECASE)
_PAGE_NUMBER_RE = re.compile(r"^-?\s*\d+\s*-?$")
_OJK_FOOTER_URL_RE = re.compile(r"https?://(?:www\.)?jdih\.ojk\.go\.id/?", re.IGNORECASE)
_EXPLANATION_BOUNDARY_RE = re.compile(r"^PENJELASAN(?:\s+ATAS)?$", re.IGNORECASE)
_ATTACHMENT_BOUNDARY_RE = re.compile(
    r"^LAMPIRAN(?:\s+(?:[IVXLCDM]+|\d+))?$",
    re.IGNORECASE,
)
_PROMULGATION_BOUNDARY_RE = re.compile(
    r"^(?:Agar(?:\s+setiap(?:\s+orang\s+mengetahuinya\b)?)?|Ditetapkan\s+di\b|Diundangkan\s+di\b)",
    re.IGNORECASE,
)
_INLINE_PROMULGATION_RE = re.compile(r"\bAgar\s+setiap\s+orang\s+mengetahuinya\b", re.IGNORECASE)
_REFERENCE_TAIL_RE = re.compile(r"\b(?P<kind>ayat|pasal|huruf|angka)\s*$", re.IGNORECASE)
_PREPOSITION_TAIL_RE = re.compile(r"\b(?:pada|dalam|di)\s*$", re.IGNORECASE)
_COMPLETE_PASAL_REFERENCE_TAIL_RE = re.compile(
    r"\bPasal\s+\d+[A-Z]?\s*$", re.IGNORECASE
)
_COMPLETE_AYAT_REFERENCE_TAIL_RE = re.compile(
    r"\bayat\s*\(\d+[a-z]?\)\s*$", re.IGNORECASE
)
_HURUF_CONJUNCTION_TAIL_RE = re.compile(
    r"\bhuruf\s+[a-z]\s+(?:dan/atau|dan|atau)\s*$", re.IGNORECASE
)
_AYAT_REFERENCE_START_RE = re.compile(
    r"^(?:ayat\s*)?\(\d+[a-z]?\)\s*(?:[,;:]|\b(?:huruf|angka)\b)", re.IGNORECASE
)
_PASAL_REFERENCE_START_RE = re.compile(
    r"^Pasal\s+\d+[A-Z]?\s+(?:ayat|huruf|angka)\b", re.IGNORECASE
)
_INLINE_PASAL_REFERENCE_RE = re.compile(
    r"^Pasal\s+\d+[A-Z]?\s*(?:[,;:]|\b(?:ayat|huruf|angka)\b)", re.IGNORECASE
)
_EXPLICIT_ACRONYM_DEFINITION_RE = re.compile(
    r"(?P<long>[A-Z][^.;:\n]{2,180}?)\s+"
    r"(?i:yang\s+selanjutnya\s+(?:disingkat|disebut)(?:\s+sebagai)?)\s+"
    r"(?P<alias>[A-Z][A-Z0-9]{1,11})\b",
)

_LEVELS = {
    "preamble": 0,
    "bab": 1,
    "section": 2,
    "point": 3,
    "subpoint": 4,
    "item": 5,
    "bagian": 2,
    "paragraf": 3,
    "pasal": 4,
    "ayat": 5,
    "huruf": 6,
    "angka": 7,
    "table": 8,
}
_PATH_TYPES = (
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
_OUTLINE_TYPES = {"section", "point", "subpoint", "item"}


@dataclass
class _Span:
    page: int | str | None
    line_start: int
    line_end: int
    lines: list[str] = field(default_factory=list)
    continuation_of: str | None = None


@dataclass
class _Unit:
    unit_type: str
    label: str
    page_start: int | str | None
    line_start: int
    path: dict[str, str]
    parent: "_Unit | None"
    ordinal: int
    node_id: str
    previous_id: str | None
    document_part: str = "normative"
    direct_lines: list[str] = field(default_factory=list)
    spans: list[_Span] = field(default_factory=list)
    children: list["_Unit"] = field(default_factory=list)

    @property
    def parent_id(self) -> str | None:
        return self.parent.node_id if self.parent else None

    def append(self, line: str, page: int | str | None, line_number: int) -> None:
        """Append a textual line, retaining a linked source span per page."""
        if not self.spans or self.spans[-1].page != page:
            prior = self.spans[-1] if self.spans else None
            self.spans.append(
                _Span(
                    page=page,
                    line_start=line_number,
                    line_end=line_number,
                    continuation_of=(
                        f"{self.node_id}:page-{prior.page}:span-{len(self.spans)}"
                        if prior
                        else None
                    ),
                )
            )
        span = self.spans[-1]
        span.line_end = line_number
        if line:
            span.lines.append(line)
            self.direct_lines.append(line)


def _page_text(page: dict[str, Any]) -> str:
    """Return raw reading-order text, falling back to Markdown for table-only pages.

    ``text`` is intentionally preferred.  It fixes the known PJP layout case
    where a converter places a Pasal below its Ayat in Markdown.  A caller can
    pass only ``markdown`` for documents whose meaningful source is a table.
    """
    return str(page.get("text") or page.get("markdown") or "")


def _is_table_line(line: str) -> bool:
    # Keep separator rows with their table.  ``markdown_table_rows`` removes
    # separators by design, so it cannot be used as the line discriminator.
    return line.count("|") >= 2


def _input_lines(pages: Iterable[dict[str, Any]]) -> Iterable[tuple[int | str | None, int, str]]:
    pending_bare_pasal: tuple[int | str | None, int, str] | None = None
    for page in pages:
        page_num = page.get("page_num")
        for line_number, raw_line in enumerate(_page_text(page).splitlines(), start=1):
            # OJK's repeating JDIH footer is sometimes emitted as a standalone
            # line and sometimes fused into the preceding legal sentence.
            # It is layout chrome, not legal evidence.
            line = normalize_space(_OJK_FOOTER_URL_RE.sub(" ", raw_line)).strip()
            if not line:
                continue
            if _BARE_PASAL_RE.fullmatch(line):
                if pending_bare_pasal:
                    yield pending_bare_pasal
                pending_bare_pasal = (page_num, line_number, line)
                continue
            if _PAGE_NUMBER_RE.fullmatch(line):
                if pending_bare_pasal:
                    pending_page, pending_line, _ = pending_bare_pasal
                    yield pending_page, pending_line, f"Pasal {line.strip('- ')}"
                    pending_bare_pasal = None
                continue
            if pending_bare_pasal:
                yield pending_bare_pasal
                pending_bare_pasal = None
            inline_boundary = _INLINE_PROMULGATION_RE.search(line)
            if inline_boundary and inline_boundary.start() > 0:
                prefix = line[: inline_boundary.start()].strip()
                suffix = line[inline_boundary.start() :].strip()
                if prefix:
                    yield page_num, line_number, prefix
                yield page_num, line_number, suffix
            else:
                yield page_num, line_number, line
    if pending_bare_pasal:
        yield pending_bare_pasal


def _document_part_boundary(line: str) -> str | None:
    """Return the document part opened by a strong legal-document boundary."""
    if _EXPLANATION_BOUNDARY_RE.fullmatch(line):
        return "explanation"
    if _PROMULGATION_BOUNDARY_RE.match(line):
        return "promulgation"
    if _ATTACHMENT_BOUNDARY_RE.fullmatch(line):
        return "attachment"
    return None


def _is_wrapped_reference_continuation(
    target: _Unit | None,
    line: str,
    candidate: tuple[str, re.Match[str], str] | None,
) -> bool:
    """Identify a wrapped citation that only resembles a new legal unit.

    PDF reading order frequently breaks ``pada ayat (1), ...`` after
    ``pada`` or ``ayat``.  The second line then matches the Ayat grammar and
    used to manufacture a duplicate node.  These checks intentionally require
    a dangling reference marker or preposition plus a reference-shaped next
    line; ordinary consecutive Ayat headings remain structural.
    """
    if target is None or candidate is None:
        return False
    direct_text = normalize_space(" ".join(target.direct_lines))
    if not direct_text:
        return False

    # A Pasal heading is normally bare.  A line that starts with ``Pasal N``
    # and immediately continues with reference syntax is an inline citation,
    # even when PDF wrapping places it at the start of a visual line.
    if candidate[0] == "pasal" and _INLINE_PASAL_REFERENCE_RE.match(line):
        return True

    tail = _REFERENCE_TAIL_RE.search(direct_text)
    if tail:
        kind = tail.group("kind").casefold()
        if kind == "ayat" and re.match(r"^(?:ayat\s*)?\(\d+[a-z]?\)", line, re.IGNORECASE):
            return True
        if kind == "pasal" and re.match(r"^(?:Pasal\s+)?\d+[A-Z]?\b", line, re.IGNORECASE):
            return True
        if kind == "huruf" and re.match(r"^(?:Huruf\s+)?[a-z](?:[.)]|\b)", line, re.IGNORECASE):
            return True
        if kind == "angka" and re.match(r"^\(?\d+[a-z]?\)?(?:[.)]|\b)", line, re.IGNORECASE):
            return True

    if _PREPOSITION_TAIL_RE.search(direct_text):
        return bool(
            re.match(
                r"^(?:ayat\s*)?\(\d+[a-z]?\)(?:\s|[,;:.]|$)",
                line,
                re.IGNORECASE,
            )
            or _PASAL_REFERENCE_START_RE.match(line)
            or re.match(r"^Pasal\s+\d+[A-Z]?\s*$", line, re.IGNORECASE)
            or re.match(r"^(?:huruf\s+)?[a-z](?:[.)]|\b)", line, re.IGNORECASE)
        )
    if _COMPLETE_PASAL_REFERENCE_TAIL_RE.search(direct_text):
        return bool(
            re.match(r"^(?:ayat\s*)?\(\d+[a-z]?\)", line, re.IGNORECASE)
            or re.match(r"^(?:huruf\s+)?[a-z](?:[.)]|\b)", line, re.IGNORECASE)
            or re.match(r"^(?:angka\s+)?\d+(?:[.)]|\b)", line, re.IGNORECASE)
        )
    if _COMPLETE_AYAT_REFERENCE_TAIL_RE.search(direct_text):
        return bool(
            re.match(r"^(?:huruf\s+)?[a-z](?:[.)]|\b)", line, re.IGNORECASE)
            or re.match(r"^(?:angka\s+)?\d+(?:[.)]|\b)", line, re.IGNORECASE)
        )
    if re.search(r"[,;]\s*$", direct_text):
        return bool(
            re.match(r"^ayat\s*\(\d+[a-z]?\)\s*[,;:]", line, re.IGNORECASE)
            or _INLINE_PASAL_REFERENCE_RE.match(line)
        )
    if _HURUF_CONJUNCTION_TAIL_RE.search(direct_text):
        return bool(re.fullmatch(r"huruf\s+[a-z]\s*\.", line, re.IGNORECASE))
    return False


def _repair_wrapped_reference_reading_order(target: _Unit | None, line: str) -> str:
    """Move a displaced Ayat marker back before its wrapped reference text.

    Some OJK PDFs emit ``(1) huruf e ... 18`` as ``huruf e ... 18(1)``.
    When the previous line ends in ``ayat``, that trailing marker is uniquely
    identifiable as the missing reference continuation and must not create a
    fabricated sibling Huruf.
    """
    if target is None:
        return line
    direct_text = normalize_space(" ".join(target.direct_lines))
    if not _REFERENCE_TAIL_RE.search(direct_text):
        return line
    if not re.match(r"^huruf\s+[a-z]\b", line, re.IGNORECASE):
        return line
    match = re.match(r"^(.*?\d)\((\d+[a-z]?)\)$", line, re.IGNORECASE)
    if not match:
        return line
    return f"({match.group(2)}) {match.group(1)}"


def _label(unit_type: str, match: re.Match[str]) -> str:
    value = normalize_space(match.group(1))
    if unit_type == "bab":
        return f"BAB {value.upper()}"
    if unit_type == "bagian":
        return f"Bagian {value}"
    if unit_type == "paragraf":
        return f"Paragraf {value}"
    if unit_type == "pasal":
        return f"Pasal {value.upper()}"
    if unit_type == "ayat":
        return f"({value.lower()})"
    if unit_type == "huruf":
        return f"huruf {value.lower()}"
    if unit_type == "angka":
        return value
    raise ValueError(f"Unsupported legal unit type: {unit_type}")


def _match_structure(line: str) -> tuple[str, re.Match[str], str] | None:
    for unit_type, pattern in (
        ("bab", _BAB_RE),
        ("bagian", _BAGIAN_RE),
        ("paragraf", _PARAGRAF_RE),
        ("pasal", _PASAL_RE),
        ("ayat", _AYAT_RE),
        ("huruf", _HURUF_WORD_RE),
    ):
        match = pattern.match(line)
        if match:
            remainder = normalize_space(match.group(2) or "") if match.lastindex and match.lastindex >= 2 else ""
            return unit_type, match, remainder

    # Bare list labels are meaningful only after a legal provision has begun.
    # The caller makes that context decision; this returns the candidate shape.
    for unit_type, pattern in (("huruf", _HURUF_RE), ("angka", _ANGKA_RE)):
        match = pattern.match(line)
        if match:
            return unit_type, match, normalize_space(match.group(2))
    return None


def _match_outline_structure(
    line: str,
    *,
    document_part: str,
    active: dict[str, "_Unit"],
) -> tuple[str, str, str] | None:
    """Match only explicit SEOJK outline labels, never inferred legal anchors."""

    if match := _OUTLINE_ROMAN_SECTION_RE.match(line):
        return "section", f"{match.group(1)}. {normalize_space(match.group(2))}", ""
    if (
        document_part == "attachment"
        and active.get("bab")
        and (match := _OUTLINE_ATTACHMENT_SECTION_RE.match(line))
    ):
        return "section", f"{match.group(1)}. {normalize_space(match.group(2))}", ""
    if active.get("section") and (match := _OUTLINE_POINT_RE.match(line)):
        return "point", match.group(1), normalize_space(match.group(2))
    if active.get("point") and (match := _OUTLINE_SUBPOINT_RE.match(line)):
        return "subpoint", match.group(1), normalize_space(match.group(2))
    if active.get("subpoint") and (match := _OUTLINE_ITEM_RE.match(line)):
        return "item", match.group(1), normalize_space(match.group(2))
    return None


def _path_key(path: dict[str, str]) -> str:
    return "/".join(f"{kind}:{path[kind]}" for kind in _PATH_TYPES if path.get(kind))


def _node_id(document_id: str, path: dict[str, str], ordinal: int) -> str:
    path_key = _path_key(path) or "preamble"
    unit_type = path.get("_type", "unit")
    seed = f"{document_id}:legal-unit:v{CHUNK_SCHEMA_VERSION}:{unit_type}:{path_key}:{ordinal}"
    return f"{slugify(seed)[:180]}-{short_hash(seed)}"


def _ancestor_for(level: int, active: dict[str, _Unit]) -> _Unit | None:
    for candidate_type in reversed(_PATH_TYPES):
        candidate = active.get(candidate_type)
        if candidate and _LEVELS[candidate_type] < level:
            return candidate
    return None


def _leaf(active: dict[str, _Unit]) -> _Unit | None:
    for unit_type in reversed((*_PATH_TYPES, "table")):
        if unit := active.get(unit_type):
            return unit
    return None


def _close_lower_levels(level: int, active: dict[str, _Unit]) -> None:
    for unit_type, unit_level in _LEVELS.items():
        if unit_level >= level:
            active.pop(unit_type, None)


def _display_text(unit: _Unit) -> str:
    lines: list[str] = []
    if unit.unit_type != "table":
        lines.append(unit.label)
    lines.extend(unit.direct_lines)
    return normalize_space(" ".join(lines)) if unit.unit_type != "table" else "\n".join(unit.direct_lines).strip()


def _truncate_context(text: str, limit: int = MAX_PARENT_LEAD_IN_CHARS) -> str:
    text = normalize_space(text)
    if len(text) <= limit:
        return text
    boundary = text.rfind(" ", 0, limit)
    return f"{text[: boundary if boundary > 0 else limit].rstrip()}…"


def _explicit_acronym_aliases(units: Iterable[_Unit]) -> dict[str, tuple[str, ...]]:
    """Return only unambiguous, explicitly declared document acronyms.

    Legal prose contains many capitalized references.  We do not infer aliases
    from initials or document titles.  A term is eligible only when the source
    itself uses ``yang selanjutnya disingkat/disebut ABC`` and ``ABC`` is a
    short all-uppercase token.  Conflicting definitions of the same acronym
    are excluded for the whole document.
    """
    aliases_by_token: dict[str, set[str]] = defaultdict(set)
    for unit in units:
        direct_text = " ".join(unit.direct_lines)
        for match in _EXPLICIT_ACRONYM_DEFINITION_RE.finditer(direct_text):
            alias = match.group("alias")
            long_form = normalize_space(match.group("long")).strip(" ,;:-")
            long_form = re.sub(r"^\d+[.)]\s*", "", long_form)
            words = long_form.split()
            if (
                alias != alias.upper()
                or len(words) < 2
                or len(words) > 16
                or len(long_form) > 180
            ):
                continue
            aliases_by_token[alias].add(long_form)

    # One acronym can be overloaded across a document.  That is not safe
    # retrieval expansion, even if each individual declaration looked valid.
    return {
        alias: tuple(sorted(long_forms, key=str.casefold))
        for alias, long_forms in aliases_by_token.items()
        if len(long_forms) == 1
    }


def _contains_term(text: str, term: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, flags=re.IGNORECASE))


def _append_retrieval_aliases(
    nodes: list[dict[str, Any]], aliases: dict[str, tuple[str, ...]]
) -> None:
    """Attach bounded document-defined aliases to search text only."""
    for node in nodes:
        retrieval_text = str(node["retrieval_text"])
        selected: list[dict[str, str]] = []
        for alias, long_forms in aliases.items():
            long_form = long_forms[0]
            if not (_contains_term(retrieval_text, alias) or _contains_term(retrieval_text, long_form)):
                continue
            # No extra text is necessary where both forms already occur.
            if _contains_term(retrieval_text, alias) and _contains_term(retrieval_text, long_form):
                continue
            selected.append({"alias": alias, "full_form": long_form})
            if len(selected) == MAX_RETRIEVAL_ALIASES_PER_UNIT:
                break
        if not selected:
            node["retrieval_aliases"] = []
            continue

        alias_text = "; ".join(f"{item['full_form']} ({item['alias']})" for item in selected)
        alias_text = _truncate_context(alias_text, MAX_RETRIEVAL_ALIAS_CHARS)
        node["retrieval_text"] = normalize_space(f"{retrieval_text} Istilah terkait: {alias_text}.")
        node["retrieval_aliases"] = selected
        # Keep this machine-readable audit data close to the retrieval source;
        # it never changes display text, citation anchors, or source spans.
        node["legal_unit"]["retrieval_aliases"] = selected


def _parent_lead_in(unit: _Unit) -> str:
    """Return the nearest meaningful Pasal/Ayat context for a legal leaf.

    A list child frequently has no subject of its own (for example ``a.
    penyediaan informasi Sumber Dana``).  The immediately governing Ayat often
    supplies that subject.  We deliberately use its *direct* prose only: no
    sibling child text, no whole-BAB duplication, and no recursive assembly.
    """
    ancestor = unit.parent
    while ancestor:
        if ancestor.unit_type in {"ayat", "pasal", "point", "subpoint"}:
            direct_text = _truncate_context(" ".join(ancestor.direct_lines))
            if direct_text:
                return direct_text
        ancestor = ancestor.parent
    return ""


def _retrieval_text(unit: _Unit) -> str:
    display = _display_text(unit)
    # BAB/Bagian/Paragraf names can be lengthy, generic, and repeated in every
    # child.  Retrieval needs the local legal anchor rather than that noise.
    context_kinds = (
        ("section", "point", "subpoint", "item")
        if unit.path.get("section")
        else ("pasal", "ayat", "huruf", "angka")
    )
    context = " > ".join(unit.path[kind] for kind in context_kinds if unit.path.get(kind))
    if unit.unit_type == "table":
        parent_context = " > ".join(
            unit.parent.path[kind]
            for kind in (
                ("section", "point", "subpoint", "item")
                if unit.parent and unit.parent.path.get("section")
                else ("pasal", "ayat", "huruf", "angka")
            )
            if unit.parent and unit.parent.path.get(kind)
        )
        return normalize_space(f"{parent_context} Tabel. {_parent_lead_in(unit)} {display}")
    parent_lead_in = (
        _parent_lead_in(unit)
        if unit.unit_type in {"huruf", "angka", "subpoint", "item"}
        else ""
    )
    if context and display:
        # Parent labels are compact navigation metadata.  The lead-in adds the
        # actual legal subject needed for lexical retrieval, without repeating
        # a complete parent tree or injecting sibling list items.
        return normalize_space(f"{context}. {parent_lead_in} {display}")
    return display


def _source_spans(unit: _Unit) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, span in enumerate(unit.spans):
        span_id = f"{unit.node_id}:page-{span.page}:span-{index + 1}"
        span_text = "\n".join(span.lines).strip()
        # ``direct_lines`` intentionally omit a structural label so display
        # text does not repeat it.  The source span, however, must remain a
        # faithful citation excerpt and therefore includes that first label.
        if index == 0 and unit.unit_type != "table":
            span_text = normalize_space(f"{unit.label} {span_text}")
        result.append(
            {
                "span_id": span_id,
                "page": span.page,
                "line_start": span.line_start,
                "line_end": span.line_end,
                "text": span_text,
                "continuation_of": span.continuation_of,
            }
        )
    return result


def _as_dict(unit: _Unit) -> dict[str, Any]:
    spans = _source_spans(unit)
    page_start = unit.spans[0].page if unit.spans else unit.page_start
    page_end = unit.spans[-1].page if unit.spans else unit.page_start
    anchors = {
        "page_start": page_start,
        "line_start": unit.spans[0].line_start if unit.spans else unit.line_start,
        "page_end": page_end,
        "line_end": unit.spans[-1].line_end if unit.spans else unit.line_start,
    }
    legal_path = {kind: unit.path[kind] for kind in _PATH_TYPES if unit.path.get(kind)}
    display_text = _display_text(unit)
    retrieval_text = _retrieval_text(unit)
    continuation = {
        "is_cross_page": len(spans) > 1,
        "span_count": len(spans),
        "links": [
            {"span_id": span["span_id"], "continuation_of": span["continuation_of"]}
            for span in spans
            if span["continuation_of"]
        ],
    }
    legal_unit = {
        "type": unit.unit_type,
        "label": unit.label,
        "document_part": unit.document_part,
        "legal_path": legal_path,
        "parent_id": unit.parent_id,
        "previous_id": unit.previous_id,
        "continuation": continuation,
        "source_spans": spans,
        "display_source_id": unit.node_id,
        "retrieval_source_id": unit.node_id,
    }
    return {
        "chunk_schema_version": CHUNK_SCHEMA_VERSION,
        "node_id": unit.node_id,
        "block_id": unit.node_id,
        "unit_type": unit.unit_type,
        "document_part": unit.document_part,
        "label": unit.label,
        "parent_id": unit.parent_id,
        "previous_id": unit.previous_id,
        "page_start": page_start,
        "page_end": page_end,
        "anchors": anchors,
        "legal_path": legal_path,
        "display_text": display_text,
        "assembled_text": display_text,
        "retrieval_text": retrieval_text,
        "source_block_ids": [unit.node_id],
        "legal_unit": legal_unit,
    }


def _aggregate_node_id(parent: _Unit, children: list[_Unit]) -> str:
    seed = f"{parent.node_id}:enumeration-aggregate:{':'.join(child.node_id for child in children)}"
    return f"{slugify(seed)[:180]}-{short_hash(seed)}"


def _aggregate_source_spans(parent: _Unit, children: list[_Unit]) -> list[dict[str, Any]]:
    source_spans: list[dict[str, Any]] = []
    for source_unit in (parent, *children):
        for span in _source_spans(source_unit):
            source_spans.append({**span, "source_node_id": source_unit.node_id})
    return source_spans


def _enumeration_aggregates(units: Iterable[_Unit]) -> list[dict[str, Any]]:
    """Build bounded, citation-ready governing-provision list aggregates.

    Atomic Huruf/Angka nodes remain the precise evidence path.  An aggregate is
    emitted only where an immediately governing Pasal, Ayat, or Huruf has a
    short direct lead-in and two or more immediate enumerated children.  This
    restores the readable ``governing sentence + complete list`` unit without
    recursively copying a whole chapter or arbitrary descendants.
    """
    aggregates: list[dict[str, Any]] = []
    for parent in units:
        if parent.unit_type not in {"pasal", "ayat", "huruf"}:
            continue
        children = [child for child in parent.children if child.unit_type in {"huruf", "angka"}]
        if not (MIN_ENUMERATION_CHILDREN <= len(children) <= MAX_ENUMERATION_CHILDREN):
            continue
        if not normalize_space(" ".join(parent.direct_lines)):
            continue

        display_text = "\n".join([_display_text(parent), *(_display_text(child) for child in children)])
        if len(display_text) > MAX_ENUMERATION_AGGREGATE_CHARS:
            continue
        source_spans = _aggregate_source_spans(parent, children)
        if not source_spans:
            continue

        node_id = _aggregate_node_id(parent, children)
        legal_path = {kind: parent.path[kind] for kind in _PATH_TYPES if parent.path.get(kind)}
        anchors = {
            "page_start": source_spans[0]["page"],
            "line_start": source_spans[0]["line_start"],
            "page_end": source_spans[-1]["page"],
            "line_end": source_spans[-1]["line_end"],
        }
        local_path = " > ".join(
            parent.path[kind]
            for kind in ("pasal", "ayat", "huruf", "angka")
            if parent.path.get(kind)
        )
        retrieval_text = normalize_space(f"{local_path}. {display_text}")
        source_block_ids = [parent.node_id, *(child.node_id for child in children)]
        continuation = {
            "is_cross_page": anchors["page_start"] != anchors["page_end"],
            "span_count": len(source_spans),
            "links": [
                {"span_id": span["span_id"], "continuation_of": span["continuation_of"]}
                for span in source_spans
                if span["continuation_of"]
            ],
        }
        legal_unit = {
            "type": "enumeration_aggregate",
            "role": "enumeration_aggregate",
            "label": f"Daftar {parent.label}",
            "document_part": parent.document_part,
            "legal_path": legal_path,
            "parent_id": parent.node_id,
            "previous_id": None,
            "continuation": continuation,
            "source_spans": source_spans,
            "display_source_id": parent.node_id,
            "retrieval_source_id": node_id,
            "citation_target_id": parent.node_id,
            "source_block_ids": source_block_ids,
        }
        aggregates.append(
            {
                "chunk_schema_version": CHUNK_SCHEMA_VERSION,
                "node_id": node_id,
                "block_id": node_id,
                "unit_type": "enumeration_aggregate",
                "legal_unit_role": "enumeration_aggregate",
                "document_part": parent.document_part,
                "label": legal_unit["label"],
                "parent_id": parent.node_id,
                "previous_id": None,
                "page_start": anchors["page_start"],
                "page_end": anchors["page_end"],
                "anchors": anchors,
                "legal_path": legal_path,
                "display_text": display_text,
                "assembled_text": display_text,
                "retrieval_text": retrieval_text,
                "source_block_ids": source_block_ids,
                "citation_target_id": parent.node_id,
                "legal_unit": legal_unit,
            }
        )
    return aggregates


def parse_legal_units(
    pages: Iterable[dict[str, Any]],
    *,
    document_id: str,
    enable_outline: bool = False,
) -> list[dict[str, Any]]:
    """Return ordered legal units from raw page text.

    The input is an iterable of already ordered page dictionaries containing
    ``page_num`` and either ``text`` or ``markdown``.  This function does no
    I/O and never consults generated corpus artifacts.  Its output is stable
    for identical input and document id.
    """
    page_list = list(pages)
    outline_index_pages = {
        page.get("page_num")
        for page in page_list
        if enable_outline and _OUTLINE_INDEX_RE.search(_page_text(page))
    }
    active: dict[str, _Unit] = {}
    all_units: list[_Unit] = []
    previous_by_parent: dict[str | None, _Unit] = {}
    ordinal_by_path: defaultdict[str, int] = defaultdict(int)
    table_lines: list[str] = []
    table_page: int | str | None = None
    table_start_line = 0
    document_part = "normative"

    def create_unit(
        unit_type: str,
        label: str,
        page: int | str | None,
        line_number: int,
        initial_text: str = "",
    ) -> _Unit:
        level = _LEVELS[unit_type]
        _close_lower_levels(level, active)
        parent = _ancestor_for(level, active)
        path = dict(parent.path) if parent else {}
        if unit_type in _PATH_TYPES:
            path[unit_type] = label
            for lower_type in _PATH_TYPES:
                if _LEVELS[lower_type] > level:
                    path.pop(lower_type, None)
        else:
            # A table inherits its owner path but is not itself a legal level.
            path = dict(parent.path) if parent else {}
        path_key = f"{unit_type}:{_path_key(path)}"
        ordinal_by_path[path_key] += 1
        ordinal = ordinal_by_path[path_key]
        node = _Unit(
            unit_type=unit_type,
            label=label,
            page_start=page,
            line_start=line_number,
            path=path,
            parent=parent,
            ordinal=ordinal,
            node_id=_node_id(document_id, {**path, "_type": unit_type}, ordinal),
            previous_id=previous_by_parent.get(parent.node_id if parent else None).node_id
            if previous_by_parent.get(parent.node_id if parent else None)
            else None,
            document_part=document_part,
        )
        previous_by_parent[parent.node_id if parent else None] = node
        if parent:
            parent.children.append(node)
        all_units.append(node)
        active[unit_type] = node
        # Every unit receives a source anchor even when its heading has no
        # trailing prose (for example a bare ``Pasal 3``).
        node.append(initial_text, page, line_number)
        return node

    def flush_table() -> None:
        nonlocal table_lines, table_page, table_start_line
        if not table_lines:
            return
        owner = _leaf(active)
        if owner and owner.unit_type == "table":
            owner = owner.parent
        # A true Markdown table stays a table node.  It never becomes a
        # fabricated Huruf merely because a cell starts with ``a.``.
        node = create_unit("table", "Tabel", table_page, table_start_line, "\n".join(table_lines))
        if owner and node.parent is not owner:
            # Tables are children of the current legal owner.  create_unit's
            # generic parent selection ignores table depth, so correct here.
            if node.parent and node in node.parent.children:
                node.parent.children.remove(node)
            node.parent = owner
            owner.children.append(node)
        active.pop("table", None)
        table_lines = []
        table_page = None
        table_start_line = 0

    for page, line_number, line in _input_lines(page_list):
        if page in outline_index_pages:
            continue
        if _is_table_line(line):
            if not table_lines:
                table_page = page
                table_start_line = line_number
            table_lines.append(line)
            continue
        flush_table()

        target = _leaf(active)
        line = _repair_wrapped_reference_reading_order(target, line)
        candidate = _match_structure(line)
        if _is_wrapped_reference_continuation(target, line, candidate):
            target.append(line, page, line_number)
            continue

        boundary_part = _document_part_boundary(line)
        if boundary_part:
            # Legal paths may repeat in PENJELASAN.  Start a new provenance
            # partition before classifying them and keep signature/promulgation
            # prose out of the terminal normative Pasal.
            active.clear()
            previous_by_parent.clear()
            document_part = boundary_part
            create_unit("preamble", "Preamble", page, line_number, line)
            continue

        outline_candidate = (
            _match_outline_structure(line, document_part=document_part, active=active)
            if enable_outline
            else None
        )
        if outline_candidate:
            unit_type, label, remainder = outline_candidate
            create_unit(unit_type, label, page, line_number, remainder)
            continue

        # Once an explicit SEOJK section opens, unlabelled lines and nested
        # parenthesized/list markers remain prose of that outline leaf.  They
        # must not be relabelled as Pasal/Ayat/Huruf.  A real BAB or Pasal may
        # still switch back into the statutory hierarchy below.
        if enable_outline and active.get("section") and not (
            candidate and candidate[0] in {"bab", "pasal"}
        ):
            if target := _leaf(active):
                target.append(line, page, line_number)
            continue

        # A numberless standalone ``Pasal`` is a damaged heading, not legal
        # prose.  Keeping it on the prior leaf manufactures a dangling
        # reference and, in explanation sections, joins unrelated provisions.
        if _BARE_PASAL_RE.fullmatch(line):
            continue

        if candidate:
            unit_type, match, remainder = candidate
            if (
                enable_outline
                and not active.get("pasal")
                and unit_type in {"bagian", "paragraf", "ayat", "huruf", "angka"}
            ):
                candidate = None
            # A plain ``a.`` or ``1.`` is only structural under an active
            # Pasal/Ayat/Huruf.  Otherwise it is ordinary preamble prose.
            if candidate and unit_type in {"huruf", "angka"} and not any(
                active.get(kind) for kind in ("pasal", "ayat", "huruf")
            ):
                candidate = None
            elif candidate:
                label = _label(unit_type, match)
                create_unit(unit_type, label, page, line_number, remainder)
                continue

        if target := _leaf(active):
            target.append(line, page, line_number)
        else:
            # Preserve non-legal opening material as an uncited preamble unit;
            # it remains non-structural and can be excluded by the pipeline.
            if not active.get("preamble"):
                create_unit("preamble", "Preamble", page, line_number)
            active["preamble"].append(line, page, line_number)

    flush_table()
    nodes = [_as_dict(unit) for unit in all_units]
    nodes.extend(_enumeration_aggregates(all_units))
    _append_retrieval_aliases(nodes, _explicit_acronym_aliases(all_units))
    return nodes
