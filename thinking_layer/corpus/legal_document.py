"""Build the versioned Legal JSON AST from normalized corpus evidence."""

from __future__ import annotations

from collections.abc import Iterable

from ..domain.legal import (
    ContextualUnit,
    ContextualUnitV1,
    CorpusLimitationV1,
    InstrumentIdentity,
    InstrumentIdentityV1,
    LegalDocumentV1,
    LegalNode,
    LegalNodeV1,
    LegalPath,
    LegalPathV1,
    LifecycleRelation,
    LifecycleRelationV1,
    MarkdownLinkV1,
    MarkdownRangeV1,
    SourceBlockV1,
    SourceDocument,
    SourceDocumentV1,
    SourceSpan,
    SourceSpanV1,
    VisualAnchorV1,
)
from .context import assemble_contextual_units
from .liteparse_normalizer import MarkdownRange, NormalizedBlock, NormalizedDocument
from .parser import ParsedDocument


def _instrument(identity: InstrumentIdentity | None) -> InstrumentIdentityV1 | None:
    if identity is None:
        return None
    return InstrumentIdentityV1(
        issuer=identity.issuer,
        instrument_type=identity.instrument_type,
        number=identity.number,
        year=identity.year,
    )


def _legal_path(path: LegalPath) -> LegalPathV1:
    return LegalPathV1(
        pasal=path.pasal,
        ayat=path.ayat,
        huruf=path.huruf,
        angka=path.angka,
        heading=path.heading,
    )


def _source_span(span: SourceSpan) -> SourceSpanV1:
    return SourceSpanV1(
        page_start=span.page_start,
        page_end=span.page_end,
        char_start=span.char_start,
        char_end=span.char_end,
    )


def _markdown_range(source_range: MarkdownRange) -> MarkdownRangeV1:
    return MarkdownRangeV1(
        page_num=source_range.page_num,
        line_start=source_range.line_start,
        line_end=source_range.line_end,
        char_start=source_range.char_start,
        char_end=source_range.char_end,
    )


def _range_for_span(markdown: str, span: SourceSpan) -> MarkdownRangeV1:
    return MarkdownRangeV1(
        page_num=span.page_start,
        line_start=markdown.count("\n", 0, span.char_start),
        line_end=markdown.count("\n", 0, span.char_end),
        char_start=span.char_start,
        char_end=span.char_end,
    )


def _source_block(block: NormalizedBlock) -> SourceBlockV1:
    anchor = block.geometry_anchor
    return SourceBlockV1(
        block_id=block.block_id,
        kind=block.kind,
        raw_markdown=block.raw_markdown,
        display_text=block.display_text,
        retrieval_text=block.retrieval_text,
        markdown_range=_markdown_range(block.source_range),
        source_pages=(block.source_range.page_num,),
        parent_block_id=block.parent_block_id,
        child_block_ids=block.child_block_ids,
        links=tuple(
            MarkdownLinkV1(
                text=link.text,
                target=link.target,
                source_range=_markdown_range(link.source_range),
            )
            for link in block.links
        ),
        zone=block.zone,
        visual_anchor=(
            VisualAnchorV1(
                page_num=anchor.page_num,
                x=anchor.x,
                y=anchor.y,
                width=anchor.width,
                height=anchor.height,
                text_item_count=anchor.text_item_count,
            )
            if anchor is not None
            else None
        ),
        quarantine_reason=block.quarantine_reason,
    )


def _blocks_for_node(
    node: LegalNode, normalized: NormalizedDocument
) -> tuple[str, ...]:
    block_ids: list[str] = []
    pages = {page.page_num: page for page in normalized.pages}
    for span in node.spans:
        page = pages[span.page_start]
        for block in page.blocks:
            source_range = block.source_range
            if (
                source_range.char_start <= span.char_start
                and span.char_end <= source_range.char_end
            ):
                block_ids.append(block.block_id)
    return tuple(dict.fromkeys(block_ids))


def _node(node: LegalNode, normalized: NormalizedDocument) -> LegalNodeV1:
    pages = {page.page_num: page for page in normalized.pages}
    raw_markdown = "\n".join(
        pages[span.page_start].raw_markdown[span.char_start : span.char_end]
        for span in node.spans
    )
    return LegalNodeV1(
        node_id=node.node_id,
        document_id=node.document_id,
        node_kind=node.node_kind,
        raw_markdown=raw_markdown,
        display_text=node.text,
        retrieval_text=node.retrieval_text,
        legal_path=_legal_path(node.legal_path),
        source_spans=tuple(_source_span(span) for span in node.spans),
        markdown_ranges=tuple(
            _range_for_span(pages[span.page_start].raw_markdown, span)
            for span in node.spans
        ),
        source_block_ids=_blocks_for_node(node, normalized),
        parent_node_id=node.parent_node_id,
    )


def _context(
    context: ContextualUnit, nodes: dict[str, LegalNodeV1]
) -> ContextualUnitV1:
    return ContextualUnitV1(
        context_id=context.context_id,
        document_id=context.document_id,
        display_text="\n\n".join(
            nodes[node_id].display_text for node_id in context.source_node_ids
        ),
        source_node_ids=context.source_node_ids,
        primary_node_id=context.primary_node_id,
        legal_path=_legal_path(context.legal_path),
        source_spans=tuple(_source_span(span) for span in context.spans),
    )


def _relation(relation: LifecycleRelation) -> LifecycleRelationV1:
    return LifecycleRelationV1(
        relation_id=relation.relation_id,
        subject_instrument=_instrument(relation.subject_instrument),
        object_instrument=_instrument(relation.object_instrument),
        kind=relation.kind.value,
        source_document_id=relation.source_document_id,
        source_node_id=relation.source_node_id,
        effective_on=relation.effective_on,
        scope_text=relation.scope_text,
    )


def legal_document_from_parsed(
    *,
    source_document: SourceDocument,
    parsed: ParsedDocument,
    contexts: Iterable[ContextualUnit] | None = None,
    lifecycle_relations: Iterable[LifecycleRelation] = (),
) -> LegalDocumentV1:
    """Create and validate one canonical AST document from source-backed evidence."""

    if parsed.normalized is None:
        raise ValueError("parsed document must retain its normalized Markdown evidence")
    normalized = parsed.normalized
    if (
        source_document.file_id != parsed.file_id
        or normalized.file_id != parsed.file_id
    ):
        raise ValueError(
            "source document and parsed Markdown evidence must share a file ID"
        )
    nodes = tuple(_node(node, normalized) for node in parsed.nodes)
    nodes_by_id = {node.node_id: node for node in nodes}
    context_values = (
        tuple(contexts) if contexts is not None else assemble_contextual_units(parsed)
    )
    limitations = tuple(
        CorpusLimitationV1(
            code="markdown_geometry_disagreement",
            message=disagreement.reason,
            references=(disagreement.block_id,),
        )
        for disagreement in parsed.geometry_disagreements
    )
    document = LegalDocumentV1(
        source_document=SourceDocumentV1(
            file_id=source_document.file_id,
            instrument=_instrument(source_document.instrument),
            title=source_document.title,
            role=source_document.role,
            raw_path=source_document.raw_path,
            source_url=source_document.source_url,
            source_sha256=source_document.source_sha256,
            lifecycle_state=source_document.lifecycle_state.value,
        ),
        source_blocks=tuple(
            _source_block(block) for page in normalized.pages for block in page.blocks
        ),
        legal_nodes=nodes,
        contextual_units=tuple(
            _context(context, nodes_by_id) for context in context_values
        ),
        lifecycle_relations=tuple(
            _relation(relation) for relation in lifecycle_relations
        ),
        limitations=limitations,
    )
    return LegalDocumentV1.model_validate(document.model_dump(mode="json"))
