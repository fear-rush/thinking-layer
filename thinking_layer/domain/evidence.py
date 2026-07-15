from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .legal import ContextualUnit, LegalNode, SourceDocument


class GateName(StrEnum):
    DOCUMENT_RELEVANCE = "document_relevance"
    CLAIM_RELEVANCE = "claim_relevance"
    LIFECYCLE = "lifecycle"
    CITATION_INTEGRITY = "citation_integrity"
    ANSWER_SHAPE = "answer_shape"
    READABILITY = "readability"
    CORPUS_SCOPE = "corpus_scope"


@dataclass(frozen=True)
class DocumentCandidate:
    document: SourceDocument
    score: float
    matched_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProvisionCandidate:
    node: LegalNode
    context: ContextualUnit
    score: float
    claim_terms: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.node.document_id != self.context.document_id:
            raise ValueError("provision node and context must belong to the same document")
        if self.node.node_id not in self.context.source_node_ids:
            raise ValueError("context must include the cited provision node")


@dataclass(frozen=True)
class EvidenceGate:
    name: GateName
    passed: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceGroup:
    document: DocumentCandidate
    provisions: tuple[ProvisionCandidate, ...]
    gates: tuple[EvidenceGate, ...]

    def __post_init__(self) -> None:
        if not self.provisions:
            raise ValueError("an evidence group requires at least one provision")
        if any(provision.node.document_id != self.document.document.file_id for provision in self.provisions):
            raise ValueError("evidence provisions must be scoped to the selected document")
