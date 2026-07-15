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
_TITLE_STOP = re.compile(
    r"\b(DENGAN\s+RAHMAT|MENIMBANG\s*:|MENGINGAT\s*:)\b", re.IGNORECASE
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
    return None


def _title_from_raw(raw_record: Mapping[str, Any]) -> str:
    pages = raw_record.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("saved raw document requires pages")
    first_page = pages[0]
    if not isinstance(first_page, Mapping):
        raise ValueError("saved raw document contains an invalid first page")
    value = first_page.get("markdown") or first_page.get("text")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("saved raw document requires first-page text")
    prefix = _TITLE_STOP.split(value, maxsplit=1)[0]
    title = _normalize(prefix)
    if not title:
        raise ValueError("saved raw document has no source-backed title")
    return title[:2_000]


def _role_for(file_id: str, title: str) -> str:
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


def catalog_raw_record(raw_record: Mapping[str, Any], raw_path: Path) -> SourceDocument:
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
    title = _title_from_raw(raw_record)
    instrument = extract_instrument_identity(title)
    return SourceDocument(
        file_id=file_id,
        instrument=instrument,
        title=title,
        role=_role_for(file_id, title),
        raw_path=relative_path,
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
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
