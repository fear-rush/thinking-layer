from __future__ import annotations

from thinking_layer.corpus.parser import parse_raw_document


def test_preserves_article_and_nested_anchor_boundaries() -> None:
    parsed = parse_raw_document(
        {
            "file_id": "fixture-pbi-3-2023",
            "pages": [
                {
                    "page_num": 1,
                    "markdown": (
                        "BAB I\nKETENTUAN UMUM\n\n"
                        "Pasal 1\n"
                        "(1) Istilah ini memiliki arti sebagai berikut.\n\n"
                        "(2) Ketentuan ini berlaku bagi bank.\n\n"
                        "Pasal 2\n"
                        "a. Bank wajib menyampaikan laporan.\n"
                    ),
                }
            ],
        }
    )

    pasal_one = next(
        node
        for node in parsed.nodes
        if node.legal_path.pasal == "1" and node.node_kind == "pasal"
    )
    ayat_one = next(node for node in parsed.nodes if node.legal_path.ayat == "1")
    ayat_two = next(node for node in parsed.nodes if node.legal_path.ayat == "2")
    huruf_a = next(node for node in parsed.nodes if node.legal_path.huruf == "a")

    assert "Pasal 1" in pasal_one.text
    assert ayat_one.parent_node_id == pasal_one.node_id
    assert ayat_two.parent_node_id == pasal_one.node_id
    assert huruf_a.legal_path.pasal == "2"
    assert "Bank wajib menyampaikan laporan." in huruf_a.text
    assert huruf_a.spans[0].page_start == 1


def test_keeps_a_cross_page_continuation_citable() -> None:
    parsed = parse_raw_document(
        {
            "file_id": "fixture-pojk-15-2025",
            "pages": [
                {
                    "page_num": 1,
                    "markdown": "Pasal 5\nKetentuan dimulai pada halaman ini.",
                },
                {
                    "page_num": 2,
                    "markdown": "Ketentuan dilanjutkan pada halaman berikutnya.",
                },
            ],
        }
    )

    continuation = next(
        node for node in parsed.nodes if node.node_kind == "continuation"
    )
    assert continuation.legal_path.pasal == "5"
    assert continuation.parent_node_id == "fixture-pojk-15-2025:page:1:char:0:pasal"
    assert "dilanjutkan" in continuation.text


def test_splits_inline_ayat_boundaries_from_saved_markdown() -> None:
    parsed = parse_raw_document(
        {
            "file_id": "fixture-inline-ayat",
            "pages": [
                {
                    "page_num": 1,
                    "markdown": "Pasal 1\n(1) Ketentuan pertama berlaku. (2) Ketentuan kedua berlaku.",
                }
            ],
        }
    )

    ayat_one = next(node for node in parsed.nodes if node.legal_path.ayat == "1")
    ayat_two = next(node for node in parsed.nodes if node.legal_path.ayat == "2")
    assert "Ketentuan pertama berlaku." in ayat_one.text
    assert "Ketentuan kedua" not in ayat_one.text
    assert "Ketentuan kedua berlaku." in ayat_two.text


def test_keeps_lowercase_ayat_cross_references_in_the_same_clause() -> None:
    parsed = parse_raw_document(
        {
            "file_id": "fixture-ayat-reference",
            "pages": [
                {
                    "page_num": 1,
                    "markdown": "Pasal 1\n(2) Layanan sebagaimana dimaksud pada\nayat (1) dikelola Bank Indonesia.",
                }
            ],
        }
    )

    ayat = next(node for node in parsed.nodes if node.legal_path.ayat == "2")
    assert "dimaksud pada ayat (1) dikelola" in ayat.retrieval_text
    assert sum(node.node_kind == "ayat" for node in parsed.nodes) == 1
