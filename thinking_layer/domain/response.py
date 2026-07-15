from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .evidence import EvidenceGate
from .legal import ContextualUnit, LegalNode, SourceDocument
from .query import AnswerMode


class ResponseStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED_SCOPE = "unsupported_scope"


@dataclass(frozen=True)
class Citation:
    citation_id: str
    node: LegalNode
    context: ContextualUnit

    def __post_init__(self) -> None:
        if self.node.node_id not in self.context.source_node_ids:
            raise ValueError("citation context must resolve to its cited node")


@dataclass(frozen=True)
class Finding:
    finding_id: str
    text: str
    citation_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("finding text is required")
        if not self.citation_ids:
            raise ValueError("a finding requires at least one citation")


@dataclass(frozen=True)
class Coverage:
    eligible_document_count: int
    skipped_ocr_document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.eligible_document_count < 0:
            raise ValueError("eligible_document_count cannot be negative")
        object.__setattr__(self, "skipped_ocr_document_ids", tuple(self.skipped_ocr_document_ids))


@dataclass(frozen=True)
class QueryResponse:
    request_id: str
    status: ResponseStatus
    mode: AnswerMode
    summary: str
    documents: tuple[SourceDocument, ...] = ()
    findings: tuple[Finding, ...] = ()
    citations: tuple[Citation, ...] = ()
    limitations: tuple[str, ...] = ()
    diagnostics: tuple[EvidenceGate, ...] = ()
    coverage: Coverage = field(default_factory=lambda: Coverage(0, ()))
    stage_timings_ms: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if not self.summary.strip():
            raise ValueError("summary is required")
        citation_ids = {citation.citation_id for citation in self.citations}
        if len(citation_ids) != len(self.citations):
            raise ValueError("citation IDs must be unique")
        for finding in self.findings:
            if not set(finding.citation_ids).issubset(citation_ids):
                raise ValueError("findings must reference response citations")
        if any(value < 0 for value in self.stage_timings_ms.values()):
            raise ValueError("stage timings cannot be negative")
