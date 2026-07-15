from __future__ import annotations

from collections.abc import Iterable

from ..domain.legal import ContextualUnit, LegalNode, SourceSpan
from .parser import ParsedDocument


def _ancestor_chain(node: LegalNode, nodes_by_id: dict[str, LegalNode]) -> tuple[LegalNode, ...]:
    chain: list[LegalNode] = []
    seen: set[str] = set()
    current = node
    while True:
        if current.node_id in seen:
            raise ValueError(f"cycle detected in legal-node ancestry at {current.node_id}")
        seen.add(current.node_id)
        chain.append(current)
        if current.parent_node_id is None:
            break
        parent = nodes_by_id.get(current.parent_node_id)
        if parent is None:
            raise ValueError(
                f"legal node {current.node_id} has unresolved parent {current.parent_node_id}"
            )
        current = parent
    return tuple(reversed(chain))


def _source_order(nodes: Iterable[LegalNode]) -> tuple[LegalNode, ...]:
    return tuple(
        sorted(
            nodes,
            key=lambda node: (
                node.spans[0].page_start,
                node.spans[0].char_start,
                node.node_id,
            ),
        )
    )


def _spans(nodes: Iterable[LegalNode]) -> tuple[SourceSpan, ...]:
    return tuple(span for node in nodes for span in node.spans)


def assemble_contextual_units(parsed: ParsedDocument) -> tuple[ContextualUnit, ...]:
    """Attach each exact legal node to its readable, source-backed governing context."""
    nodes_by_id = {node.node_id: node for node in parsed.nodes}
    if len(nodes_by_id) != len(parsed.nodes):
        raise ValueError(f"parsed document {parsed.file_id} has duplicate node IDs")

    contexts: list[ContextualUnit] = []
    for node in parsed.nodes:
        governing_nodes = _source_order(_ancestor_chain(node, nodes_by_id))
        contexts.append(
            ContextualUnit(
                context_id=f"context:{node.node_id}",
                document_id=parsed.file_id,
                display_text="\n\n".join(item.text for item in governing_nodes),
                source_node_ids=tuple(item.node_id for item in governing_nodes),
                primary_node_id=node.node_id,
                legal_path=node.legal_path,
                spans=_spans(governing_nodes),
            )
        )
    return tuple(contexts)
