from __future__ import annotations

from collections.abc import Mapping

import pytest

from thinking_layer.corpus.liteparse_normalizer import normalize_raw_document
from thinking_layer.corpus.parser import parse_raw_document


@pytest.fixture
def raw_record() -> Mapping[str, object]:
    return {
        "file_id": "fixture-normalizer",
        "pages": [
            {
                "page_num": 1,
                "markdown": (
                    "## BAB I\n\n"
                    "Ketentuan [umum](https://example.test/general).\n\n"
                    "1. Dokumen pertama\n"
                    "   - Dokumen turunan\n\n"
                    "| Jenis | Batas |\n"
                    "| --- | --- |\n"
                    "| A | [10%](https://example.test/limit) |\n"
                ),
            }
        ],
    }


def test_retains_raw_slices_and_tree_structure(
    raw_record: Mapping[str, object],
) -> None:
    normalized = normalize_raw_document(raw_record)
    page = normalized.pages[0]
    heading = next(block for block in page.blocks if block.kind == "heading")
    ordered_list = next(block for block in page.blocks if block.kind == "ordered_list")
    list_item = next(block for block in page.blocks if block.kind == "list_item")
    table = next(block for block in page.blocks if block.kind == "table")
    cells = [
        block
        for block in page.blocks
        if block.kind in {"table_header_cell", "table_cell"}
    ]

    assert heading.raw_markdown == "## BAB I\n"
    assert heading.display_text == "BAB I"
    assert list_item.block_id in ordered_list.child_block_ids
    assert (
        table.raw_markdown
        == "| Jenis | Batas |\n| --- | --- |\n| A | [10%](https://example.test/limit) |\n"
    )
    assert [cell.raw_markdown for cell in cells] == [
        "Jenis",
        "Batas",
        "A",
        "[10%](https://example.test/limit)",
    ]

    for block in page.blocks:
        source = block.source_range
        assert (
            page.raw_markdown[source.char_start : source.char_end] == block.raw_markdown
        )


def test_preserves_links_with_exact_source_ranges(
    raw_record: Mapping[str, object],
) -> None:
    page = normalize_raw_document(raw_record).pages[0]
    paragraph = next(block for block in page.blocks if block.kind == "paragraph")
    link = paragraph.links[0]

    assert (link.text, link.target) == ("umum", "https://example.test/general")
    assert (
        page.raw_markdown[link.source_range.char_start : link.source_range.char_end]
        == "[umum](https://example.test/general)"
    )


def test_table_cells_cannot_become_legal_numbered_provisions() -> None:
    parsed = parse_raw_document(
        {
            "file_id": "fixture-table-boundary",
            "pages": [
                {
                    "page_num": 1,
                    "markdown": "Pasal 1\nKetentuan berlaku.\n\n| Angka | Uraian |\n| --- | --- |\n| 1. | Bukan ketentuan legal |\n",
                }
            ],
        }
    )

    assert not any(node.legal_path.angka == "1" for node in parsed.nodes)


def test_preserves_and_parses_fenced_liteparse_text_without_fence_syntax() -> None:
    raw = {
        "file_id": "fixture-fenced-layout-text",
        "pages": [
            {"page_num": 1, "markdown": "```\nPasal 7\nBank wajib melapor.\n```\n"}
        ],
    }

    normalized = normalize_raw_document(raw)
    block = next(
        block for block in normalized.pages[0].blocks if block.kind == "verbatim_block"
    )
    parsed = parse_raw_document(raw)
    article = next(node for node in parsed.nodes if node.node_kind == "pasal")

    assert block.raw_markdown == "```\nPasal 7\nBank wajib melapor.\n```\n"
    assert article.text == "Pasal 7 Bank wajib melapor."
