from __future__ import annotations

import pytest
from pydantic import ValidationError

from thinking_layer.corpus.audit import (
    audit_legal_documents,
    audit_quarantine_reporting,
)
from thinking_layer.corpus.context import assemble_contextual_units
from thinking_layer.corpus.legal_document import legal_document_from_parsed
from thinking_layer.corpus.parser import parse_raw_document
from thinking_layer.domain.legal import LegalDocumentV1, SourceDocument


def _document(file_id: str) -> SourceDocument:
    return SourceDocument(
        file_id=file_id,
        instrument=None,
        title="Fixture legal document",
        role="primary_regulation",
        raw_path=f"tests/fixtures/{file_id}.json",
        source_sha256="a" * 64,
    )


def test_serializes_clean_text_with_raw_markdown_provenance() -> None:
    raw = {
        "file_id": "fixture-legal-document",
        "pages": [
            {"page_num": 1, "markdown": "# **Pasal 1**\n\nBank wajib **melapor**."}
        ],
    }
    parsed = parse_raw_document(raw)

    artifact = legal_document_from_parsed(
        source_document=_document(raw["file_id"]),
        parsed=parsed,
        contexts=assemble_contextual_units(parsed),
    )

    assert artifact.schema_version == "legal-document-v1"
    assert artifact.source_blocks[0].raw_markdown.startswith("# **Pasal 1**")
    assert artifact.source_blocks[0].display_text == "Pasal 1"
    assert artifact.source_blocks[0].retrieval_text == "Pasal 1"
    assert all("**" not in node.display_text for node in artifact.legal_nodes)
    assert LegalDocumentV1.model_validate_json(artifact.model_dump_json()) == artifact


def test_rejects_nodes_that_reference_unknown_source_blocks() -> None:
    raw = {
        "file_id": "fixture-invalid-legal-document",
        "pages": [{"page_num": 1, "markdown": "Pasal 1\nBank wajib melapor."}],
    }
    parsed = parse_raw_document(raw)
    artifact = legal_document_from_parsed(
        source_document=_document(raw["file_id"]),
        parsed=parsed,
    )
    invalid = artifact.model_dump(mode="json")
    invalid["legal_nodes"][0]["source_block_ids"] = ["missing-block"]

    with pytest.raises(ValidationError, match="unresolved source block"):
        LegalDocumentV1.model_validate(invalid)


def test_preserves_harvested_source_url_without_rewriting_it() -> None:
    raw = {
        "file_id": "fixture-source-url",
        "pages": [{"page_num": 1, "markdown": "Pasal 1\nBank wajib melapor."}],
    }
    source_url = "https://ease.bi.go.id/helps/Matriks Self Assesment.pdf"
    artifact = legal_document_from_parsed(
        source_document=SourceDocument(
            file_id=raw["file_id"],
            instrument=None,
            title="Fixture legal document",
            role="primary_regulation",
            raw_path="tests/fixtures/source-url.json",
            source_sha256="a" * 64,
            source_url=source_url,
        ),
        parsed=parse_raw_document(raw),
    )

    assert artifact.source_document.source_url == source_url


def test_audits_schema_validity_markdown_leakage_and_quarantine_reporting() -> None:
    raw = {
        "file_id": "fixture-audit-legal-document",
        "pages": [{"page_num": 1, "markdown": "Pasal 1\nBank wajib melapor."}],
    }
    parsed = parse_raw_document(raw)
    artifact = legal_document_from_parsed(
        source_document=_document(raw["file_id"]), parsed=parsed
    )
    invalid = artifact.model_dump(mode="json")
    invalid["legal_nodes"][0]["source_block_ids"] = ["missing-block"]
    invalid_codes = {finding.code for finding in audit_legal_documents((invalid,))}
    assert invalid_codes == {"legal_document_schema_invalid"}

    leaky = artifact.model_dump(mode="json")
    leaky["legal_nodes"][0]["display_text"] = "**leaked**"
    leaky["legal_nodes"][0]["retrieval_text"] = "**leaked**"
    leakage_codes = {finding.code for finding in audit_legal_documents((leaky,))}
    assert "invalid_display_text" in leakage_codes

    report_codes = {
        finding.code
        for finding in audit_quarantine_reporting(
            source_document_ids=(raw["file_id"],),
            quarantined_sources=((raw["file_id"], "geometry mismatch"),),
            geometry_disagreements=(),
        )
    }
    assert report_codes == {"quarantined_source_published"}


def test_audit_does_not_mistake_literal_legal_footnote_markers_for_markdown() -> None:
    raw = {
        "file_id": "fixture-footnote-marker",
        "pages": [{"page_num": 1, "markdown": "Pasal 1\nBank wajib melapor."}],
    }
    artifact = legal_document_from_parsed(
        source_document=_document(raw["file_id"]), parsed=parse_raw_document(raw)
    )
    serialized = artifact.model_dump(mode="json")
    serialized["legal_nodes"][0]["display_text"] = "Keterangan **)"
    serialized["legal_nodes"][0]["retrieval_text"] = "Keterangan **)"

    assert not audit_legal_documents((serialized,))


def test_audit_does_not_join_adjacent_literal_footnote_markers_as_bold_markdown() -> None:
    raw = {
        "file_id": "fixture-adjacent-footnote-markers",
        "pages": [{"page_num": 1, "markdown": "Pasal 1\nBank wajib melapor."}],
    }
    artifact = legal_document_from_parsed(
        source_document=_document(raw["file_id"]), parsed=parse_raw_document(raw)
    )
    serialized = artifact.model_dump(mode="json")
    text = "Keterangan **) : rincian ***) : lanjutan"
    serialized["legal_nodes"][0]["display_text"] = text
    serialized["legal_nodes"][0]["retrieval_text"] = text

    assert not audit_legal_documents((serialized,))


def test_audit_does_not_mistake_triple_and_quadruple_footnote_markers_for_bold() -> None:
    raw = {
        "file_id": "fixture-long-footnote-markers",
        "pages": [{"page_num": 1, "markdown": "Pasal 1\nBank wajib melapor."}],
    }
    artifact = legal_document_from_parsed(
        source_document=_document(raw["file_id"]), parsed=parse_raw_document(raw)
    )
    serialized = artifact.model_dump(mode="json")
    text = "Keterangan *** rincian footnote *** dan ****rincian berikutnya"
    serialized["legal_nodes"][0]["display_text"] = text
    serialized["legal_nodes"][0]["retrieval_text"] = text

    assert not audit_legal_documents((serialized,))


def test_audit_does_not_mistake_fill_in_blank_underscores_for_emphasis() -> None:
    raw = {
        "file_id": "fixture-fill-in-blanks",
        "pages": [{"page_num": 1, "markdown": "Pasal 1\nBank wajib melapor."}],
    }
    artifact = legal_document_from_parsed(
        source_document=_document(raw["file_id"]), parsed=parse_raw_document(raw)
    )
    serialized = artifact.model_dump(mode="json")
    text = "Kepada: _____________________ Dari: _____________________"
    serialized["legal_nodes"][0]["display_text"] = text
    serialized["legal_nodes"][0]["retrieval_text"] = text

    assert not audit_legal_documents((serialized,))


def test_audit_does_not_mistake_escaped_footnote_markers_after_words_for_bold() -> None:
    raw = {
        "file_id": "fixture-escaped-footnote-markers",
        "pages": [{"page_num": 1, "markdown": "Pasal 1\nBank wajib melapor."}],
    }
    artifact = legal_document_from_parsed(
        source_document=_document(raw["file_id"]), parsed=parse_raw_document(raw)
    )
    serialized = artifact.model_dump(mode="json")
    text = "Jumlah konsumen** Rp xxx,- Dst **) total dana"
    serialized["legal_nodes"][0]["display_text"] = text
    serialized["legal_nodes"][0]["retrieval_text"] = text

    assert not audit_legal_documents((serialized,))
