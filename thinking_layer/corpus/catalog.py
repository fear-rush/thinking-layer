from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config.paths import ROOT
from ..domain.legal import InstrumentIdentity, SourceDocument
from .eligibility import OcrEligibility
from .liteparse_normalizer import NormalizedDocument, normalize_raw_document


_SPACE = re.compile(r"\s+")
_PBI_LEGACY = re.compile(
    r"(?:PERATURAN\s+BANK\s+INDONESIA|PBI)\s+(?:NOMOR\s+)?(\d+/\d+/PBI)/(\d{4})",
    re.IGNORECASE,
)
_INSTRUMENT_YEAR = re.compile(
    r"\b(PBI|POJK|SEOJK|PADG|SEBI)\s+(?:NOMOR\s+)?(\d+(?:/[A-Z.0-9]+)?)\s+(?:TAHUN\s+)?(\d{4})\b",
    re.IGNORECASE,
)
_OJK_LONG_FORM = re.compile(
    r"(PERATURAN|SURAT\s+EDARAN)\s+OT[O0]RITAS\s+JASA\s+KEUANGAN.*?\bNOMOR\s+(\d+)"
    r"(?:/([A-Z.0-9]+))?(?:\s+TAHUN\s+|/)(\d{4})\b",
    re.IGNORECASE,
)
_BAPEPAM_DECISION = re.compile(
    r"\bKEP(?:UTUSAN)?[-\s]+(\d+)/(PM|BL)/(\d{4})\b", re.IGNORECASE
)
_TITLE_STOP = re.compile(
    r"\b(DENGAN\s+RAHMAT|MENIMBANG\s*:|MENGINGAT\s*:)", re.IGNORECASE
)
_TITLE_LEAD = re.compile(
    r"\b(?:PERATURAN|KEPUTUSAN|SURAT\s+EDARAN|UNDANG-UNDANG|PBI|POJK|SEOJK|"
    r"PADG|SEBI|KETENTUAN|PEDOMAN|DOKUMEN|FAQ|FREQUENTLY)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Catalog:
    source_documents: tuple[SourceDocument, ...]

    def __post_init__(self) -> None:
        file_ids = [document.file_id for document in self.source_documents]
        identity_keys = [document.identity_key for document in self.source_documents]
        if len(file_ids) != len(set(file_ids)):
            raise ValueError("source-document file IDs must be unique")
        if len(identity_keys) != len(set(identity_keys)):
            raise ValueError("source-document identity keys must be unique")

    @property
    def uncatalogued_file_ids(self) -> tuple[str, ...]:
        return tuple(
            document.file_id
            for document in self.source_documents
            if document.instrument is None
        )

    @property
    def instruments(self) -> tuple[InstrumentIdentity, ...]:
        seen: dict[str, InstrumentIdentity] = {}
        for document in self.source_documents:
            if document.instrument is not None:
                seen.setdefault(document.instrument.key, document.instrument)
        return tuple(seen.values())


def _normalize(value: str) -> str:
    return _SPACE.sub(" ", value).strip()


def extract_instrument_identity(source_text: str) -> InstrumentIdentity | None:
    """Recognize an explicit legal-instrument identity from source text."""
    normalized = _normalize(source_text)
    if match := _PBI_LEGACY.search(normalized):
        return InstrumentIdentity("BI", "PBI", match.group(1), int(match.group(2)))
    if match := _OJK_LONG_FORM.search(normalized):
        form, number, suffix, year = match.groups()
        instrument_type = "POJK" if form.upper().startswith("PERATURAN") else "SEOJK"
        display_number = "/".join(part for part in (number, suffix) if part)
        return InstrumentIdentity("OJK", instrument_type, display_number, int(year))
    if match := _INSTRUMENT_YEAR.search(normalized):
        instrument_type, number, year = match.groups()
        issuer = "BI" if instrument_type.upper() in {"PBI", "PADG", "SEBI"} else "OJK"
        return InstrumentIdentity(issuer, instrument_type.upper(), number, int(year))
    if match := _BAPEPAM_DECISION.search(normalized):
        number, office, year = match.groups()
        issuer = "BAPEPAM-LK" if office.upper() == "BL" else "BAPEPAM"
        return InstrumentIdentity(issuer, "KEP", f"{number}/{office.upper()}", int(year))
    return None


def _title_from_normalized(normalized: NormalizedDocument) -> str:
    """Use normalized, top-level first-page evidence for a catalog title."""

    candidates: list[str] = []
    seen: set[str] = set()
    for block in normalized.pages[0].blocks:
        if block.kind not in {
            "heading",
            "paragraph",
            "verbatim_block",
            "table_header_cell",
            "table_cell",
        }:
            continue
        if (
            block.display_text
            and block.display_text not in seen
            and not _TITLE_STOP.match(block.display_text)
        ):
            candidates.append(block.display_text)
            seen.add(block.display_text)
    start = next(
        (index for index, value in enumerate(candidates) if _TITLE_LEAD.search(value)),
        0,
    )
    values: list[str] = []
    for value in candidates[start:]:
        prefix = _TITLE_STOP.split(value, maxsplit=1)[0]
        if prefix:
            values.append(prefix)
        if _TITLE_STOP.search(value) or len(values) >= 3:
            break
    title = _normalize(" ".join(values))
    if not title:
        raise ValueError("normalized document has no source-backed title")
    return title[:500]


def _role_for(file_id: str, title: str, family: str) -> str:
    if family == "faq":
        return "secondary_faq"
    if family == "explanation":
        return "explanation"
    if family == "attachment":
        return "attachment"
    if family == "circular":
        return "circular"
    normalized = f"{file_id} {title}".casefold()
    if "faq" in normalized or "frequently asked" in normalized:
        return "secondary_faq"
    if "abstrak" in normalized or "summary" in normalized or "ringkasan" in normalized:
        return "secondary_summary"
    if "penjelasan" in normalized:
        return "explanation"
    if "lampiran" in normalized or "attachment" in normalized:
        return "attachment"
    if "seojk" in normalized or "sebi" in normalized or "surat edaran" in normalized:
        return "circular"
    return "primary_regulation"


def catalog_normalized_record(
    raw_record: Mapping[str, Any], raw_path: Path, normalized: NormalizedDocument
) -> SourceDocument:
    file_id = raw_record.get("file_id")
    if not isinstance(file_id, str) or not file_id.strip():
        raise ValueError(f"saved raw document requires file_id: {raw_path}")
    try:
        relative_path = raw_path.resolve().relative_to(ROOT).as_posix()
    except ValueError as error:
        raise ValueError(
            f"saved raw path must be inside the repository: {raw_path}"
        ) from error
    source_bytes = raw_path.read_bytes()
    if normalized.file_id != file_id:
        raise ValueError("catalog normalization file ID does not match raw record")
    title = _title_from_normalized(normalized)
    instrument = extract_instrument_identity(title)
    source_url = raw_record.get("source_url")
    return SourceDocument(
        file_id=file_id,
        instrument=instrument,
        title=title,
        role=_role_for(file_id, title, normalized.family),
        raw_path=relative_path,
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        source_url=source_url if isinstance(source_url, str) and source_url else None,
    )


def catalog_raw_record(raw_record: Mapping[str, Any], raw_path: Path) -> SourceDocument:
    """Catalog a raw record through the same quality-checked normalizer as builds."""

    return catalog_normalized_record(
        raw_record, raw_path, normalize_raw_document(raw_record)
    )


def build_catalog(paths: Iterable[Path], eligibility: OcrEligibility) -> Catalog:
    documents: list[SourceDocument] = []
    for path in sorted(paths):
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
            continue
        eligibility.validate_raw_record(raw_record)
        documents.append(catalog_raw_record(raw_record, path))
    return Catalog(source_documents=tuple(documents))
