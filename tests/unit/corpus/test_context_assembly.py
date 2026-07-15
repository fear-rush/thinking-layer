from __future__ import annotations

from thinking_layer.corpus.context import assemble_contextual_units
from thinking_layer.corpus.parser import parse_raw_document


def test_includes_governing_lead_in_without_unrelated_siblings() -> None:
    parsed = parse_raw_document(
        {
            "file_id": "fixture-pojk-15-2025",
            "pages": [
                {
                    "page_num": 1,
                    "markdown": (
                        "Pasal 1\n"
                        "(1) Ketentuan pertama berlaku.\n\n"
                        "(2) Ketentuan kedua berlaku.\n\n"
                        "Pasal 2\n"
                        "(1) Ketentuan lain berlaku."
                    ),
                }
            ],
        }
    )

    contexts = assemble_contextual_units(parsed)
    ayat_two = next(
        node
        for node in parsed.nodes
        if node.legal_path.pasal == "1" and node.legal_path.ayat == "2"
    )
    context = next(
        item for item in contexts if item.primary_node_id == ayat_two.node_id
    )

    assert context.source_node_ids == (ayat_two.parent_node_id, ayat_two.node_id)
    assert "Pasal 1" in context.display_text
    assert "Ketentuan kedua berlaku." in context.display_text
    assert "Ketentuan pertama berlaku." not in context.display_text
    assert "Pasal 2" not in context.display_text


def test_keeps_cross_page_ancestor_and_continuation_spans() -> None:
    parsed = parse_raw_document(
        {
            "file_id": "fixture-pbi-3-2023",
            "pages": [
                {
                    "page_num": 1,
                    "markdown": "Pasal 5\nKetentuan dimulai di halaman pertama.",
                },
                {"page_num": 2, "markdown": "Ketentuan selesai di halaman kedua."},
            ],
        }
    )

    contexts = assemble_contextual_units(parsed)
    continuation = next(
        node for node in parsed.nodes if node.node_kind == "continuation"
    )
    context = next(
        item for item in contexts if item.primary_node_id == continuation.node_id
    )

    assert context.source_node_ids[-1] == continuation.node_id
    assert [span.page_start for span in context.spans] == [1, 2]
    assert "Pasal 5" in context.display_text
    assert "halaman kedua" in context.display_text
