from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from pydantic import ValidationError

from ..common.text import normalize_space
from ..domain.legal import (
    ContextualUnit,
    LegalDocumentV1,
    LegalNode,
    LifecycleRelation,
    SourceDocument,
)
from .lifecycle import LifecycleGraph


_DANGLING_END = re.compile(
    r"\b(?:sebagaimana\s+dimaksud\s+(?:dalam|pada)|berdasarkan|sesuai\s+dengan)\s*$",
    re.IGNORECASE,
)
_MARKDOWN_PRESENTATION = re.compile(
    r"(?m)^\s{0,3}#{1,6}\s|\*\*[^*\n]+\*\*|__[^_\n]+__|`[^`\n]+`|\[[^\]]+\]\([^)]*\)"
)


@dataclass(frozen=True)
class AuditFinding:
    code: str
    message: str
    references: tuple[str, ...] = ()


@dataclass(frozen=True)
class CorpusAudit:
    findings: tuple[AuditFinding, ...]
    document_count: int
    node_count: int
    context_count: int
    lifecycle_relation_count: int

    @property
    def passed(self) -> bool:
        return not self.findings


def _invalid_spans(reference: str, spans: Iterable[object]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    previous_page = 0
    for index, span in enumerate(spans):
        page_start = getattr(span, "page_start", None)
        page_end = getattr(span, "page_end", None)
        char_start = getattr(span, "char_start", None)
        char_end = getattr(span, "char_end", None)
        if (
            not isinstance(page_start, int)
            or not isinstance(page_end, int)
            or not isinstance(char_start, int)
            or not isinstance(char_end, int)
            or page_start < 1
            or page_end < page_start
            or char_start < 0
            or char_end < char_start
        ):
            findings.append(
                AuditFinding(
                    code="invalid_source_span",
                    message=f"{reference} has an invalid source span at position {index}",
                    references=(reference,),
                )
            )
        elif page_start < previous_page:
            findings.append(
                AuditFinding(
                    code="unordered_source_span",
                    message=f"{reference} source spans are not in page order",
                    references=(reference,),
                )
            )
        previous_page = max(
            previous_page, page_start if isinstance(page_start, int) else 0
        )
    return findings


def audit_corpus(
    *,
    source_documents: Iterable[SourceDocument],
    nodes: Iterable[LegalNode],
    contexts: Iterable[ContextualUnit],
    lifecycle_relations: Iterable[LifecycleRelation],
) -> CorpusAudit:
    documents = tuple(source_documents)
    legal_nodes = tuple(nodes)
    contextual_units = tuple(contexts)
    relations = tuple(lifecycle_relations)
    findings: list[AuditFinding] = []

    documents_by_id: dict[str, SourceDocument] = {}
    document_identity_keys: set[str] = set()
    for document in documents:
        if document.file_id in documents_by_id:
            findings.append(
                AuditFinding(
                    code="duplicate_source_document_id",
                    message=f"duplicate source document ID: {document.file_id}",
                    references=(document.file_id,),
                )
            )
        documents_by_id[document.file_id] = document
        if document.identity_key in document_identity_keys:
            findings.append(
                AuditFinding(
                    code="duplicate_source_document_identity",
                    message=f"duplicate source document identity: {document.file_id}",
                    references=(document.file_id,),
                )
            )
        document_identity_keys.add(document.identity_key)

    nodes_by_id: dict[str, LegalNode] = {}
    parent_node_ids = {
        node.parent_node_id for node in legal_nodes if node.parent_node_id is not None
    }
    for node in legal_nodes:
        if node.node_id in nodes_by_id:
            findings.append(
                AuditFinding(
                    code="duplicate_legal_node_id",
                    message=f"duplicate legal node ID: {node.node_id}",
                    references=(node.node_id,),
                )
            )
        nodes_by_id[node.node_id] = node
        if node.document_id not in documents_by_id:
            findings.append(
                AuditFinding(
                    code="unresolved_node_document",
                    message=f"legal node {node.node_id} has no source document",
                    references=(node.node_id, node.document_id),
                )
            )
        if node.node_id not in parent_node_ids and _DANGLING_END.search(node.text):
            findings.append(
                AuditFinding(
                    code="dangling_fragment",
                    message=f"legal node {node.node_id} ends in an incomplete legal reference",
                    references=(node.node_id,),
                )
            )
        findings.extend(_invalid_spans(node.node_id, node.spans))

    for node in legal_nodes:
        if node.parent_node_id is not None and node.parent_node_id not in nodes_by_id:
            findings.append(
                AuditFinding(
                    code="unresolved_parent_node",
                    message=f"legal node {node.node_id} has an unresolved parent",
                    references=(node.node_id, node.parent_node_id),
                )
            )

    context_ids: set[str] = set()
    for context in contextual_units:
        if context.context_id in context_ids:
            findings.append(
                AuditFinding(
                    code="duplicate_context_id",
                    message=f"duplicate contextual unit ID: {context.context_id}",
                    references=(context.context_id,),
                )
            )
        context_ids.add(context.context_id)
        primary = nodes_by_id.get(context.primary_node_id)
        if primary is None:
            findings.append(
                AuditFinding(
                    code="unresolved_context_primary_node",
                    message=f"context {context.context_id} has an unresolved primary node",
                    references=(context.context_id, context.primary_node_id),
                )
            )
        else:
            if primary.document_id != context.document_id:
                findings.append(
                    AuditFinding(
                        code="context_document_mismatch",
                        message=f"context {context.context_id} does not match its primary node document",
                        references=(context.context_id, primary.node_id),
                    )
                )
            if (
                primary.parent_node_id is not None
                and primary.parent_node_id not in context.source_node_ids
            ):
                findings.append(
                    AuditFinding(
                        code="missing_governing_lead_in",
                        message=f"context {context.context_id} omits its primary node parent",
                        references=(context.context_id, primary.parent_node_id),
                    )
                )
        for source_node_id in context.source_node_ids:
            if source_node_id not in nodes_by_id:
                findings.append(
                    AuditFinding(
                        code="unresolved_context_source_node",
                        message=f"context {context.context_id} has an unresolved source node",
                        references=(context.context_id, source_node_id),
                    )
                )
        findings.extend(_invalid_spans(context.context_id, context.spans))

    for relation in relations:
        if relation.source_document_id not in documents_by_id:
            findings.append(
                AuditFinding(
                    code="unresolved_lifecycle_source_document",
                    message=f"lifecycle relation {relation.relation_id} has an unresolved source document",
                    references=(relation.relation_id, relation.source_document_id),
                )
            )
        source_node = nodes_by_id.get(relation.source_node_id)
        if source_node is None:
            findings.append(
                AuditFinding(
                    code="unresolved_lifecycle_source_node",
                    message=f"lifecycle relation {relation.relation_id} has an unresolved source node",
                    references=(relation.relation_id, relation.source_node_id),
                )
            )
        elif source_node.document_id != relation.source_document_id:
            findings.append(
                AuditFinding(
                    code="lifecycle_provenance_mismatch",
                    message=f"lifecycle relation {relation.relation_id} source node belongs to another document",
                    references=(relation.relation_id, relation.source_node_id),
                )
            )

    try:
        LifecycleGraph(relations)
    except ValueError as error:
        findings.append(
            AuditFinding(
                code="lifecycle_cycle",
                message=str(error),
                references=tuple(relation.relation_id for relation in relations),
            )
        )

    return CorpusAudit(
        findings=tuple(findings),
        document_count=len(documents),
        node_count=len(legal_nodes),
        context_count=len(contextual_units),
        lifecycle_relation_count=len(relations),
    )


def audit_legal_documents(
    documents: Iterable[object],
) -> tuple[AuditFinding, ...]:
    """Verify published Legal JSON AST instances and display-text invariants."""

    findings: list[AuditFinding] = []
    for index, candidate in enumerate(documents):
        try:
            serialized = (
                candidate.model_dump(mode="json")
                if isinstance(candidate, LegalDocumentV1)
                else candidate
            )
            document = LegalDocumentV1.model_validate(serialized)
        except ValidationError as error:
            for detail in error.errors():
                location = ".".join(str(part) for part in detail["loc"])
                findings.append(
                    AuditFinding(
                        code="legal_document_schema_invalid",
                        message=f"serialized legal document {index} is invalid at {location}: {detail['msg']}",
                        references=(str(index), location),
                    )
                )
            continue

        for block in document.source_blocks:
            findings.extend(
                _text_findings(
                    reference=block.block_id,
                    display_text=block.display_text,
                    retrieval_text=block.retrieval_text,
                )
            )
        for node in document.legal_nodes:
            findings.extend(
                _text_findings(
                    reference=node.node_id,
                    display_text=node.display_text,
                    retrieval_text=node.retrieval_text,
                )
            )
        for context in document.contextual_units:
            findings.extend(
                _text_findings(
                    reference=context.context_id,
                    display_text=context.display_text,
                    retrieval_text=None,
                )
            )
    return tuple(findings)


def _text_findings(
    *, reference: str, display_text: str, retrieval_text: str | None
) -> tuple[AuditFinding, ...]:
    findings: list[AuditFinding] = []
    if _MARKDOWN_PRESENTATION.search(display_text):
        findings.append(
            AuditFinding(
                code="raw_markdown_leakage",
                message=f"{reference} exposes Markdown presentation syntax in display text",
                references=(reference,),
            )
        )
    if retrieval_text is not None:
        if _MARKDOWN_PRESENTATION.search(retrieval_text):
            findings.append(
                AuditFinding(
                    code="raw_markdown_leakage",
                    message=f"{reference} exposes Markdown presentation syntax in retrieval text",
                    references=(reference,),
                )
            )
        if retrieval_text != normalize_space(display_text):
            findings.append(
                AuditFinding(
                    code="invalid_retrieval_text",
                    message=f"{reference} retrieval text is not normalized display text",
                    references=(reference,),
                )
            )
    return tuple(findings)


def audit_quarantine_reporting(
    *,
    source_document_ids: Iterable[str],
    quarantined_sources: Iterable[tuple[str, str]],
    geometry_disagreements: Iterable[tuple[str, str, str]],
) -> tuple[AuditFinding, ...]:
    """Ensure quarantined source evidence is reportable but never publishable."""

    published_ids = set(source_document_ids)
    findings: list[AuditFinding] = []
    quarantined = tuple(quarantined_sources)
    quarantined_ids = {file_id for file_id, _ in quarantined}
    for file_id, reason in quarantined:
        if not file_id or not reason.strip():
            findings.append(
                AuditFinding(
                    code="invalid_quarantine_report",
                    message="quarantined sources require a file ID and reason",
                    references=tuple(item for item in (file_id,) if item),
                )
            )
        if file_id in published_ids:
            findings.append(
                AuditFinding(
                    code="quarantined_source_published",
                    message=f"quarantined source {file_id} was published",
                    references=(file_id,),
                )
            )
    for file_id, block_id, reason in geometry_disagreements:
        if not file_id or not block_id or not reason.strip():
            findings.append(
                AuditFinding(
                    code="invalid_geometry_disagreement_report",
                    message="geometry disagreements require file ID, block ID, and reason",
                    references=tuple(item for item in (file_id, block_id) if item),
                )
            )
        if file_id in quarantined_ids or file_id in published_ids:
            continue
        findings.append(
            AuditFinding(
                code="unaccounted_geometry_disagreement",
                message=f"geometry disagreement for unknown source {file_id}",
                references=(file_id, block_id),
            )
        )
    return tuple(findings)
