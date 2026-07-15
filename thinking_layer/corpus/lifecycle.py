from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from ..domain.legal import (
    InstrumentIdentity,
    LegalNode,
    LifecycleKind,
    LifecycleRelation,
    LifecycleState,
    SourceDocument,
)


_LEGACY_PBI = re.compile(
    r"(?:PERATURAN\s+BANK\s+INDONESIA|PBI)\s+(?:NOMOR\s+)?(\d+/\d+/PBI)/(\d{4})",
    re.IGNORECASE,
)
_INSTRUMENT_REFERENCE = re.compile(
    r"\b(PBI|POJK|SEOJK|PADG|SEBI)\s+(?:NOMOR\s+)?"
    r"(\d+(?:/[A-Z.0-9]+)?)\s+(?:TAHUN\s+|/)(\d{4})\b",
    re.IGNORECASE,
)
_AMENDS = re.compile(r"\b(?:PERUBAHAN(?:\s+(?:PERTAMA|KEDUA|KETIGA|KEEMPAT))?\s+ATAS|MENGUBAH)\b", re.IGNORECASE)
_REVOKES = re.compile(r"\b(?:MENCABUT|DICABUT|DINYATAKAN\s+TIDAK\s+BERLAKU)\b", re.IGNORECASE)
_SUPERSEDES = re.compile(r"\b(?:MENGGANTIKAN|DIGANTIKAN\s+OLEH)\b", re.IGNORECASE)
_PARTIAL_SCOPE = re.compile(r"\b(?:SEPANJANG|UNTUK\s+BAGIAN|KECUALI\s+KETENTUAN)\b", re.IGNORECASE)
_STATEMENT_BOUNDARY = re.compile(r"(?<=[.;])\s+")


@dataclass(frozen=True)
class LifecycleGraph:
    relations: tuple[LifecycleRelation, ...]

    def __post_init__(self) -> None:
        relation_ids = [relation.relation_id for relation in self.relations]
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("lifecycle relation IDs must be unique")
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        edges: dict[str, set[str]] = {}
        for relation in self.relations:
            edges.setdefault(relation.subject_instrument.key, set()).add(
                relation.object_instrument.key
            )

        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []

        def visit(identity_key: str) -> None:
            if identity_key in visiting:
                cycle_start = stack.index(identity_key)
                cycle = [*stack[cycle_start:], identity_key]
                raise ValueError(f"lifecycle relations contain a cycle: {' -> '.join(cycle)}")
            if identity_key in visited:
                return
            visiting.add(identity_key)
            stack.append(identity_key)
            for target in edges.get(identity_key, ()):
                visit(target)
            stack.pop()
            visiting.remove(identity_key)
            visited.add(identity_key)

        for identity_key in edges:
            visit(identity_key)

    def state_for(self, instrument: InstrumentIdentity) -> LifecycleState:
        affected = [
            relation
            for relation in self.relations
            if relation.object_instrument.key == instrument.key
        ]
        if any(relation.kind is LifecycleKind.REVOKES for relation in affected):
            return LifecycleState.REVOKED
        if any(relation.kind is LifecycleKind.PARTIALLY_REVOKES for relation in affected):
            return LifecycleState.PARTIALLY_REVOKED
        if any(relation.kind is LifecycleKind.SUPERSEDES for relation in affected):
            return LifecycleState.SUPERSEDED
        if any(relation.kind is LifecycleKind.AMENDS for relation in affected):
            return LifecycleState.AMENDED
        return LifecycleState.UNKNOWN


def _references(text: str) -> tuple[InstrumentIdentity, ...]:
    references: dict[str, InstrumentIdentity] = {}
    for match in _LEGACY_PBI.finditer(text):
        identity = InstrumentIdentity("BI", "PBI", match.group(1), int(match.group(2)))
        references.setdefault(identity.key, identity)
    for match in _INSTRUMENT_REFERENCE.finditer(text):
        instrument_type, number, year = match.groups()
        normalized_type = instrument_type.upper()
        issuer = "BI" if normalized_type in {"PBI", "PADG", "SEBI"} else "OJK"
        identity = InstrumentIdentity(issuer, normalized_type, number, int(year))
        references.setdefault(identity.key, identity)
    return tuple(references.values())


def _kind_for(text: str) -> LifecycleKind | None:
    if _REVOKES.search(text):
        if _PARTIAL_SCOPE.search(text):
            return LifecycleKind.PARTIALLY_REVOKES
        return LifecycleKind.REVOKES
    if _SUPERSEDES.search(text):
        return LifecycleKind.SUPERSEDES
    if _AMENDS.search(text):
        return LifecycleKind.AMENDS
    return None


def _statements(text: str) -> tuple[str, ...]:
    return tuple(statement.strip() for statement in _STATEMENT_BOUNDARY.split(text) if statement.strip())


def extract_lifecycle_relations(
    source_document: SourceDocument,
    nodes: Iterable[LegalNode],
) -> tuple[LifecycleRelation, ...]:
    """Derive lifecycle relations only when a parsed source node states both effect and target."""
    if source_document.instrument is None or source_document.role != "primary_regulation":
        return ()

    relations: list[LifecycleRelation] = []
    seen: set[tuple[str, str, str]] = set()
    for node in nodes:
        if node.document_id != source_document.file_id:
            raise ValueError(
                f"lifecycle node {node.node_id} does not belong to {source_document.file_id}"
            )
        for statement in _statements(node.text):
            kind = _kind_for(statement)
            if kind is None:
                continue
            for target in _references(statement):
                if target.key == source_document.instrument.key:
                    continue
                key = (node.node_id, kind.value, target.key)
                if key in seen:
                    continue
                seen.add(key)
                scope_text = statement if kind is LifecycleKind.PARTIALLY_REVOKES else None
                relations.append(
                    LifecycleRelation(
                        relation_id=f"lifecycle:{node.node_id}:{kind.value}:{target.key}",
                        subject_instrument=source_document.instrument,
                        object_instrument=target,
                        kind=kind,
                        source_document_id=source_document.file_id,
                        source_node_id=node.node_id,
                        scope_text=scope_text,
                    )
                )
    return tuple(relations)
