from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from hashlib import sha256
from pathlib import PurePosixPath


def _required(value: str, field_name: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _key_part(value: str) -> str:
    return "-".join("".join(character for character in value.casefold() if character.isalnum()).split())


class LifecycleKind(StrEnum):
    AMENDS = "amends"
    REVOKES = "revokes"
    SUPERSEDES = "supersedes"
    PARTIALLY_REVOKES = "partially_revokes"


class LifecycleState(StrEnum):
    ACTIVE = "active"
    AMENDED = "amended"
    REVOKED = "revoked"
    PARTIALLY_REVOKED = "partially_revoked"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class InstrumentIdentity:
    issuer: str
    instrument_type: str
    number: str
    year: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "issuer", _required(self.issuer, "issuer"))
        object.__setattr__(self, "instrument_type", _required(self.instrument_type, "instrument_type"))
        object.__setattr__(self, "number", _required(self.number, "number"))
        if self.year < 1900 or self.year > 3000:
            raise ValueError("year must be a four-digit legal-instrument year")

    @property
    def key(self) -> str:
        return ":".join(
            (
                _key_part(self.issuer),
                _key_part(self.instrument_type),
                _key_part(self.number),
                str(self.year),
            )
        )


@dataclass(frozen=True)
class SourceSpan:
    page_start: int
    page_end: int
    char_start: int
    char_end: int

    def __post_init__(self) -> None:
        if self.page_start < 1 or self.page_end < self.page_start:
            raise ValueError("source span pages must be positive and ordered")
        if self.char_start < 0 or self.char_end < self.char_start:
            raise ValueError("source span characters must be ordered")


@dataclass(frozen=True)
class LegalPath:
    pasal: str | None = None
    ayat: str | None = None
    huruf: str | None = None
    angka: str | None = None
    heading: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "heading", tuple(_required(item, "heading item") for item in self.heading))

    @property
    def anchor(self) -> str:
        parts = [
            f"Pasal {self.pasal}" if self.pasal else None,
            f"Ayat {self.ayat}" if self.ayat else None,
            f"Huruf {self.huruf}" if self.huruf else None,
            f"Angka {self.angka}" if self.angka else None,
        ]
        return " ".join(part for part in parts if part)


@dataclass(frozen=True)
class SourceDocument:
    file_id: str
    instrument: InstrumentIdentity | None
    title: str
    role: str
    raw_path: str
    source_sha256: str
    lifecycle_state: LifecycleState = LifecycleState.UNKNOWN

    def __post_init__(self) -> None:
        object.__setattr__(self, "file_id", _required(self.file_id, "file_id"))
        object.__setattr__(self, "title", _required(self.title, "title"))
        object.__setattr__(self, "role", _required(self.role, "role"))
        raw_path = PurePosixPath(self.raw_path)
        if raw_path.is_absolute() or ".." in raw_path.parts:
            raise ValueError("raw_path must be a repository-relative path")
        object.__setattr__(self, "raw_path", raw_path.as_posix())
        digest = self.source_sha256.lower()
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError("source_sha256 must be a SHA-256 digest")
        object.__setattr__(self, "source_sha256", digest)

    @property
    def identity_key(self) -> str:
        instrument_key = self.instrument.key if self.instrument is not None else "unclassified"
        material = f"{instrument_key}\0{self.file_id}\0{self.role}\0{self.source_sha256}"
        return sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LifecycleRelation:
    relation_id: str
    subject_instrument: InstrumentIdentity
    object_instrument: InstrumentIdentity
    kind: LifecycleKind
    source_document_id: str
    source_node_id: str
    effective_on: date | None = None
    scope_text: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "relation_id", _required(self.relation_id, "relation_id"))
        object.__setattr__(self, "source_document_id", _required(self.source_document_id, "source_document_id"))
        object.__setattr__(self, "source_node_id", _required(self.source_node_id, "source_node_id"))
        if self.subject_instrument == self.object_instrument:
            raise ValueError("a lifecycle relation cannot target the same instrument")
        if self.kind is LifecycleKind.PARTIALLY_REVOKES and not _required(
            self.scope_text or "", "scope_text"
        ):
            raise ValueError("partial revocation requires source-backed scope_text")


@dataclass(frozen=True)
class LegalNode:
    node_id: str
    document_id: str
    node_kind: str
    text: str
    retrieval_text: str
    legal_path: LegalPath
    spans: tuple[SourceSpan, ...]
    parent_node_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", _required(self.node_id, "node_id"))
        object.__setattr__(self, "document_id", _required(self.document_id, "document_id"))
        object.__setattr__(self, "node_kind", _required(self.node_kind, "node_kind"))
        object.__setattr__(self, "text", _required(self.text, "text"))
        object.__setattr__(self, "retrieval_text", _required(self.retrieval_text, "retrieval_text"))
        if not self.spans:
            raise ValueError("a legal node requires at least one source span")
        object.__setattr__(self, "spans", tuple(self.spans))


@dataclass(frozen=True)
class ContextualUnit:
    context_id: str
    document_id: str
    display_text: str
    source_node_ids: tuple[str, ...]
    primary_node_id: str
    legal_path: LegalPath
    spans: tuple[SourceSpan, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "context_id", _required(self.context_id, "context_id"))
        object.__setattr__(self, "document_id", _required(self.document_id, "document_id"))
        object.__setattr__(self, "display_text", _required(self.display_text, "display_text"))
        source_node_ids = tuple(_required(node_id, "source_node_id") for node_id in self.source_node_ids)
        if not source_node_ids:
            raise ValueError("a contextual unit requires source nodes")
        if self.primary_node_id not in source_node_ids:
            raise ValueError("primary_node_id must be one of source_node_ids")
        if not self.spans:
            raise ValueError("a contextual unit requires source spans")
        object.__setattr__(self, "source_node_ids", source_node_ids)
        object.__setattr__(self, "spans", tuple(self.spans))
