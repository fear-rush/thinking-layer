from __future__ import annotations

import pytest

from thinking_layer.corpus.liteparse_normalizer import normalize_raw_document
from thinking_layer.corpus.parser import QuarantinedDocumentError, parse_raw_document


def _fresh_page(markdown: str, *geometry_text: str) -> dict[str, object]:
    return {
        "page_num": 1,
        "markdown": markdown,
        "text": markdown,
        "text_items": [
            {
                "text": text,
                "x": index * 10,
                "y": 10,
                "width": max(len(text), 1) * 4,
                "height": 10,
            }
            for index, text in enumerate(geometry_text)
        ],
    }


def test_regulation_blocks_are_normative_and_get_geometry_anchors() -> None:
    raw = {
        "contract": "thinking-layer-fresh-liteparse-v1",
        "file_id": "fixture-pojk-regulation",
        "source_path": "downloads/peraturan-ojk/POJK 1.pdf",
        "pages": [
            _fresh_page(
                "PERATURAN OTORITAS JASA KEUANGAN\n\nPasal 1\nBank wajib melapor.",
                "PERATURAN OTORITAS JASA KEUANGAN",
                "Pasal 1",
                "Bank wajib melapor.",
            )
        ],
    }

    normalized = normalize_raw_document(raw)
    parsed = parse_raw_document(raw)

    assert normalized.family == "regulation"
    assert all(block.zone == "normative" for block in normalized.pages[0].blocks)
    assert any(
        block.geometry_anchor is not None
        for block in normalized.pages[0].blocks
        if block.kind == "paragraph"
    )
    assert any(node.legal_path.pasal == "1" for node in parsed.nodes)


def test_faq_numbering_is_not_a_legal_path() -> None:
    raw = {
        "contract": "thinking-layer-fresh-liteparse-v1",
        "file_id": "fixture-faq",
        "source_path": "downloads/peraturan-ojk/FAQ POJK 1.pdf",
        "pages": [
            _fresh_page(
                "# 1. Kapan aturan berlaku?\n\nAturan berlaku pada tanggal ditetapkan.",
                "1. Kapan aturan berlaku?",
                "Aturan berlaku pada tanggal ditetapkan.",
            )
        ],
    }

    normalized = normalize_raw_document(raw)
    parsed = parse_raw_document(raw)

    assert normalized.family == "faq"
    assert {block.zone for block in normalized.pages[0].blocks} == {"faq"}
    assert not any(node.legal_path.anchor for node in parsed.nodes)


def test_geometry_disagreement_quarantines_instead_of_guessing() -> None:
    raw = {
        "contract": "thinking-layer-fresh-liteparse-v1",
        "file_id": "fixture-geometry-mismatch",
        "source_path": "downloads/peraturan-ojk/POJK 1.pdf",
        "pages": [
            _fresh_page(
                "PERATURAN OTORITAS JASA KEUANGAN\n\nPasal 1\nBank wajib melapor.",
                "teks tata letak yang tidak terkait",
            )
        ],
    }

    normalized = normalize_raw_document(raw)

    assert normalized.geometry_disagreements
    assert all(
        block.quarantine_reason is not None
        for block in normalized.pages[0].blocks
        if block.kind in {"heading", "paragraph"}
    )
    with pytest.raises(QuarantinedDocumentError, match="geometry validation"):
        parse_raw_document(raw)


def test_empty_liteparse_layout_fence_is_quarantined() -> None:
    raw = {
        "file_id": "fixture-empty-layout-fence",
        "pages": [{"page_num": 1, "markdown": "```text\n\n```"}],
    }

    with pytest.raises(QuarantinedDocumentError, match="no_citable_normalized_content"):
        parse_raw_document(raw)
