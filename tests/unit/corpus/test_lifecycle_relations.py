from __future__ import annotations

import pytest

from thinking_layer.corpus.lifecycle import LifecycleGraph, extract_lifecycle_relations
from thinking_layer.domain.legal import (
    InstrumentIdentity,
    LegalNode,
    LegalPath,
    LifecycleKind,
    LifecycleRelation,
    LifecycleState,
    SourceDocument,
    SourceSpan,
)


def _source_document(instrument: InstrumentIdentity) -> SourceDocument:
    return SourceDocument(
        file_id="bi-pbi-15-7-2013",
        instrument=instrument,
        title="Peraturan Bank Indonesia Nomor 15/7/PBI/2013",
        role="primary_regulation",
        raw_path="processed/raw/liteparse/bi-pbi-15-7-2013.json",
        source_sha256="a" * 64,
    )


def _source_node(text: str) -> LegalNode:
    return LegalNode(
        node_id="bi-pbi-15-7-2013:page:1:char:0:preamble",
        document_id="bi-pbi-15-7-2013",
        node_kind="preamble",
        text=text,
        retrieval_text=text,
        legal_path=LegalPath(),
        spans=(SourceSpan(1, 1, 0, len(text)),),
    )


def test_derives_source_backed_amendment_and_state() -> None:
    amending = InstrumentIdentity("BI", "PBI", "15/7/PBI", 2013)
    document = _source_document(amending)
    node = _source_node(
        "PERUBAHAN KEDUA ATAS PERATURAN BANK INDONESIA NOMOR 12/19/PBI/2010"
    )

    relations = extract_lifecycle_relations(document, (node,))
    graph = LifecycleGraph(relations)

    assert len(relations) == 1
    relation = relations[0]
    assert relation.kind is LifecycleKind.AMENDS
    assert relation.source_node_id == node.node_id
    assert (
        graph.state_for(InstrumentIdentity("BI", "PBI", "12/19/PBI", 2010))
        is LifecycleState.AMENDED
    )
    assert graph.state_for(amending) is LifecycleState.UNKNOWN


def test_partial_revocation_keeps_the_source_scope() -> None:
    document = _source_document(InstrumentIdentity("BI", "PBI", "3", 2023))
    node = _source_node(
        "MENCABUT PBI NOMOR 2 TAHUN 2020 SEPANJANG MENGENAI PELAPORAN BULANAN."
    )

    relation = extract_lifecycle_relations(document, (node,))[0]

    assert relation.kind is LifecycleKind.PARTIALLY_REVOKES
    assert relation.scope_text == node.text


def test_rejects_cycles_and_keeps_absent_status_unknown() -> None:
    first = InstrumentIdentity("BI", "PBI", "1", 2020)
    second = InstrumentIdentity("BI", "PBI", "2", 2020)
    relation = LifecycleRelation(
        relation_id="one",
        subject_instrument=first,
        object_instrument=second,
        kind=LifecycleKind.AMENDS,
        source_document_id="one",
        source_node_id="one:node",
    )
    reverse = LifecycleRelation(
        relation_id="two",
        subject_instrument=second,
        object_instrument=first,
        kind=LifecycleKind.AMENDS,
        source_document_id="two",
        source_node_id="two:node",
    )

    with pytest.raises(ValueError, match="cycle"):
        LifecycleGraph((relation, reverse))
    assert LifecycleGraph(()).state_for(first) is LifecycleState.UNKNOWN
