from __future__ import annotations

import unittest

from thinking_layer.corpus.audit import audit_corpus
from thinking_layer.corpus.context import assemble_contextual_units
from thinking_layer.corpus.parser import parse_raw_document
from thinking_layer.domain.legal import (
    ContextualUnit,
    InstrumentIdentity,
    LegalPath,
    SourceDocument,
)


def document(file_id: str = "fixture-pbi-3-2023") -> SourceDocument:
    return SourceDocument(
        file_id=file_id,
        instrument=InstrumentIdentity("BI", "PBI", "3", 2023),
        title="Peraturan Bank Indonesia Nomor 3 Tahun 2023",
        role="primary_regulation",
        raw_path="processed/raw/liteparse/fixture-pbi-3-2023.json",
        source_sha256="a" * 64,
    )


class StructuralAuditTest(unittest.TestCase):
    def test_accepts_resolved_readable_corpus_objects(self) -> None:
        parsed = parse_raw_document(
            {
                "file_id": "fixture-pbi-3-2023",
                "pages": [{"page_num": 1, "markdown": "Pasal 1\n(1) Bank wajib melapor."}],
            }
        )
        audit = audit_corpus(
            source_documents=(document(),),
            nodes=parsed.nodes,
            contexts=assemble_contextual_units(parsed),
            lifecycle_relations=(),
        )

        self.assertTrue(audit.passed)

    def test_reports_dangling_fragment_and_missing_lead_in(self) -> None:
        parsed = parse_raw_document(
            {
                "file_id": "fixture-pbi-3-2023",
                "pages": [
                    {
                        "page_num": 1,
                        "markdown": "Pasal 1\n(1) Ketentuan berlaku sebagaimana dimaksud dalam",
                    }
                ],
            }
        )
        ayat = next(node for node in parsed.nodes if node.legal_path.ayat == "1")
        incomplete_context = ContextualUnit(
            context_id="context:incomplete",
            document_id=ayat.document_id,
            display_text=ayat.text,
            source_node_ids=(ayat.node_id,),
            primary_node_id=ayat.node_id,
            legal_path=LegalPath(pasal="1", ayat="1"),
            spans=ayat.spans,
        )

        audit = audit_corpus(
            source_documents=(document(),),
            nodes=parsed.nodes,
            contexts=(incomplete_context,),
            lifecycle_relations=(),
        )
        codes = {finding.code for finding in audit.findings}

        self.assertIn("dangling_fragment", codes)
        self.assertIn("missing_governing_lead_in", codes)

    def test_reports_unresolved_context_source(self) -> None:
        parsed = parse_raw_document(
            {
                "file_id": "fixture-pbi-3-2023",
                "pages": [{"page_num": 1, "markdown": "Pasal 1\nBank wajib melapor."}],
            }
        )
        node = parsed.nodes[0]
        context = ContextualUnit(
            context_id="context:unresolved",
            document_id=node.document_id,
            display_text=node.text,
            source_node_ids=(node.node_id, "missing-node"),
            primary_node_id=node.node_id,
            legal_path=node.legal_path,
            spans=node.spans,
        )

        audit = audit_corpus(
            source_documents=(document(),),
            nodes=parsed.nodes,
            contexts=(context,),
            lifecycle_relations=(),
        )

        self.assertIn("unresolved_context_source_node", {finding.code for finding in audit.findings})


if __name__ == "__main__":
    unittest.main()
