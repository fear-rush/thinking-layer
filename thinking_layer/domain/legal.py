from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


LEGAL_DOCUMENT_SCHEMA_VERSION = "legal-document-v1"


class _ArtifactModel(BaseModel):
    """Immutable, closed serialized-corpus boundary model."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class InstrumentIdentityV1(_ArtifactModel):
    issuer: str = Field(min_length=1)
    instrument_type: str = Field(min_length=1)
    number: str = Field(min_length=1)
    year: int = Field(ge=1900, le=3000)


class SourceDocumentV1(_ArtifactModel):
    file_id: str = Field(min_length=1)
    instrument: InstrumentIdentityV1 | None = None
    title: str = Field(min_length=1)
    role: str = Field(min_length=1)
    raw_path: str = Field(min_length=1)
    source_url: str | None = None
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    lifecycle_state: str = Field(min_length=1)


class MarkdownRangeV1(_ArtifactModel):
    page_num: int = Field(ge=1)
    line_start: int = Field(ge=0)
    line_end: int = Field(ge=0)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)

    @model_validator(mode="after")
    def _ordered(self) -> MarkdownRangeV1:
        if self.line_end < self.line_start or self.char_end < self.char_start:
            raise ValueError(
                "Markdown ranges must have ordered line and character bounds"
            )
        return self


class SourceSpanV1(_ArtifactModel):
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)

    @model_validator(mode="after")
    def _ordered(self) -> SourceSpanV1:
        if self.page_end < self.page_start or self.char_end < self.char_start:
            raise ValueError("Source spans must have ordered page and character bounds")
        return self


class VisualAnchorV1(_ArtifactModel):
    page_num: int = Field(ge=1)
    x: float
    y: float
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    text_item_count: int = Field(ge=1)


class MarkdownLinkV1(_ArtifactModel):
    text: str = Field(min_length=1)
    target: str = Field(min_length=1)
    source_range: MarkdownRangeV1


class LegalPathV1(_ArtifactModel):
    pasal: str | None = None
    ayat: str | None = None
    huruf: str | None = None
    angka: str | None = None
    heading: tuple[str, ...] = ()


class SourceBlockV1(_ArtifactModel):
    block_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    raw_markdown: str
    display_text: str
    retrieval_text: str
    markdown_range: MarkdownRangeV1
    source_pages: tuple[int, ...] = Field(min_length=1)
    parent_block_id: str | None = None
    child_block_ids: tuple[str, ...] = ()
    links: tuple[MarkdownLinkV1, ...] = ()
    zone: str = Field(min_length=1)
    visual_anchor: VisualAnchorV1 | None = None
    quarantine_reason: str | None = None


class LegalNodeV1(_ArtifactModel):
    node_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    node_kind: str = Field(min_length=1)
    raw_markdown: str = Field(min_length=1)
    display_text: str = Field(min_length=1)
    retrieval_text: str = Field(min_length=1)
    legal_path: LegalPathV1
    source_spans: tuple[SourceSpanV1, ...] = Field(min_length=1)
    markdown_ranges: tuple[MarkdownRangeV1, ...] = Field(min_length=1)
    source_block_ids: tuple[str, ...] = Field(min_length=1)
    parent_node_id: str | None = None


class ContextualUnitV1(_ArtifactModel):
    context_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    display_text: str = Field(min_length=1)
    source_node_ids: tuple[str, ...] = Field(min_length=1)
    primary_node_id: str = Field(min_length=1)
    legal_path: LegalPathV1
    source_spans: tuple[SourceSpanV1, ...] = Field(min_length=1)


class LifecycleRelationV1(_ArtifactModel):
    relation_id: str = Field(min_length=1)
    subject_instrument: InstrumentIdentityV1
    object_instrument: InstrumentIdentityV1
    kind: str = Field(min_length=1)
    source_document_id: str = Field(min_length=1)
    source_node_id: str = Field(min_length=1)
    effective_on: date | None = None
    scope_text: str | None = None


class CorpusLimitationV1(_ArtifactModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    references: tuple[str, ...] = ()


class LegalDocumentV1(_ArtifactModel):
    """Versioned, self-validating canonical corpus artifact."""

    schema_version: Literal["legal-document-v1"] = LEGAL_DOCUMENT_SCHEMA_VERSION
    source_document: SourceDocumentV1
    source_blocks: tuple[SourceBlockV1, ...] = Field(min_length=1)
    legal_nodes: tuple[LegalNodeV1, ...] = Field(min_length=1)
    contextual_units: tuple[ContextualUnitV1, ...]
    lifecycle_relations: tuple[LifecycleRelationV1, ...]
    limitations: tuple[CorpusLimitationV1, ...] = ()

    @model_validator(mode="after")
    def _validate_references(self) -> LegalDocumentV1:
        block_ids = {block.block_id for block in self.source_blocks}
        node_ids = {node.node_id for node in self.legal_nodes}
        if len(block_ids) != len(self.source_blocks):
            raise ValueError("source block IDs must be unique within a LegalDocumentV1")
        if len(node_ids) != len(self.legal_nodes):
            raise ValueError("legal node IDs must be unique within a LegalDocumentV1")
        document_id = self.source_document.file_id
        for node in self.legal_nodes:
            if node.document_id != document_id:
                raise ValueError(
                    f"legal node {node.node_id} belongs to another document"
                )
            if not set(node.source_block_ids) <= block_ids:
                raise ValueError(
                    f"legal node {node.node_id} has an unresolved source block"
                )
            if node.parent_node_id is not None and node.parent_node_id not in node_ids:
                raise ValueError(f"legal node {node.node_id} has an unresolved parent")
        for context in self.contextual_units:
            if context.document_id != document_id:
                raise ValueError(
                    f"context {context.context_id} belongs to another document"
                )
            if context.primary_node_id not in node_ids:
                raise ValueError(
                    f"context {context.context_id} has an unresolved primary node"
                )
            if not set(context.source_node_ids) <= node_ids:
                raise ValueError(
                    f"context {context.context_id} has an unresolved source node"
                )
        for relation in self.lifecycle_relations:
            if relation.source_document_id != document_id:
                raise ValueError(
                    f"lifecycle relation {relation.relation_id} belongs to another document"
                )
            if relation.source_node_id not in node_ids:
                raise ValueError(
                    f"lifecycle relation {relation.relation_id} has an unresolved source node"
                )
        return self


def _required(value: str, field_name: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _key_part(value: str) -> str:
    return "-".join(
        "".join(
            character for character in value.casefold() if character.isalnum()
        ).split()
    )


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
        object.__setattr__(
            self, "instrument_type", _required(self.instrument_type, "instrument_type")
        )
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
        object.__setattr__(
            self,
            "heading",
            tuple(_required(item, "heading item") for item in self.heading),
        )

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
    source_url: str | None = None
    lifecycle_state: LifecycleState = LifecycleState.UNKNOWN

    def __post_init__(self) -> None:
        object.__setattr__(self, "file_id", _required(self.file_id, "file_id"))
        object.__setattr__(self, "title", _required(self.title, "title"))
        object.__setattr__(self, "role", _required(self.role, "role"))
        raw_path = PurePosixPath(self.raw_path)
        if raw_path.is_absolute() or ".." in raw_path.parts:
            raise ValueError("raw_path must be a repository-relative path")
        object.__setattr__(self, "raw_path", raw_path.as_posix())
        if self.source_url is not None and not isinstance(self.source_url, str):
            raise ValueError("source_url must be a harvested string or None")
        digest = self.source_sha256.lower()
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError("source_sha256 must be a SHA-256 digest")
        object.__setattr__(self, "source_sha256", digest)

    @property
    def identity_key(self) -> str:
        instrument_key = (
            self.instrument.key if self.instrument is not None else "unclassified"
        )
        material = (
            f"{instrument_key}\0{self.file_id}\0{self.role}\0{self.source_sha256}"
        )
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
        object.__setattr__(
            self, "relation_id", _required(self.relation_id, "relation_id")
        )
        object.__setattr__(
            self,
            "source_document_id",
            _required(self.source_document_id, "source_document_id"),
        )
        object.__setattr__(
            self, "source_node_id", _required(self.source_node_id, "source_node_id")
        )
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
        object.__setattr__(
            self, "document_id", _required(self.document_id, "document_id")
        )
        object.__setattr__(self, "node_kind", _required(self.node_kind, "node_kind"))
        object.__setattr__(self, "text", _required(self.text, "text"))
        object.__setattr__(
            self, "retrieval_text", _required(self.retrieval_text, "retrieval_text")
        )
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
        object.__setattr__(
            self, "document_id", _required(self.document_id, "document_id")
        )
        object.__setattr__(
            self, "display_text", _required(self.display_text, "display_text")
        )
        source_node_ids = tuple(
            _required(node_id, "source_node_id") for node_id in self.source_node_ids
        )
        if not source_node_ids:
            raise ValueError("a contextual unit requires source nodes")
        if self.primary_node_id not in source_node_ids:
            raise ValueError("primary_node_id must be one of source_node_ids")
        if not self.spans:
            raise ValueError("a contextual unit requires source spans")
        object.__setattr__(self, "source_node_ids", source_node_ids)
        object.__setattr__(self, "spans", tuple(self.spans))
