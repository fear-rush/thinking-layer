from __future__ import annotations

import json
from pathlib import Path

import pytest

from thinking_layer.corpus.liteparse_normalizer import normalize_raw_document
from thinking_layer.corpus.catalog import catalog_raw_record
from thinking_layer.corpus.parser import parse_raw_document


FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "fresh_liteparse"
FIXTURE_NAMES = (
    "bi_regulation",
    "ojk_regulation",
    "explanation",
    "attachment_table",
    "circular",
    "faq",
)
LEGAL_FIXTURES = {"bi_regulation", "ojk_regulation"}


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixtures_are_literal_minimized_fresh_liteparse_records(name: str) -> None:
    raw = _fixture(name)
    options = raw["liteparse_options"]
    pages = raw["pages"]

    assert raw["contract"] == "thinking-layer-fresh-liteparse-v1"
    assert raw["liteparse_version"] == "2.4.0"
    assert options == {
        "emit_word_boxes": True,
        "extract_links": True,
        "image_mode": "off",
        "ocr_enabled": False,
        "output_format": "markdown",
        "quiet": True,
    }
    assert len(pages) == 1
    page = pages[0]
    assert page["markdown"]
    assert page["text"]
    assert page["text_items"]


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_normalization_preserves_the_fresh_fixture_source_ranges(name: str) -> None:
    normalized = normalize_raw_document(_fixture(name))
    page = normalized.pages[0]

    assert page.blocks
    for block in page.blocks:
        source_range = block.source_range
        assert (
            page.raw_markdown[source_range.char_start : source_range.char_end]
            == block.raw_markdown
        )


@pytest.mark.parametrize("name", LEGAL_FIXTURES)
def test_regulation_fixtures_have_source_backed_legal_anchors(name: str) -> None:
    parsed = parse_raw_document(_fixture(name))

    assert any(node.legal_path.pasal is not None for node in parsed.nodes)


def test_circular_fixture_remains_citable_without_an_invented_legal_path() -> None:
    parsed = parse_raw_document(_fixture("circular"))

    assert any("KETENTUAN PENUTUP" in node.text for node in parsed.nodes)
    assert not any(node.legal_path.angka is not None for node in parsed.nodes)


def test_attachment_table_retains_table_context_without_creating_a_legal_number() -> (
    None
):
    raw = _fixture("attachment_table")
    normalized = normalize_raw_document(raw)
    parsed = parse_raw_document(raw)

    assert any(block.kind == "table" for block in normalized.pages[0].blocks)
    assert not any(node.legal_path.angka is not None for node in parsed.nodes)


def test_faq_heading_is_not_interpreted_as_a_numbered_legal_provision() -> None:
    parsed = parse_raw_document(_fixture("faq"))

    assert not any(node.legal_path.angka is not None for node in parsed.nodes)


@pytest.mark.parametrize(
    ("name", "role"),
    (
        ("bi_regulation", "primary_regulation"),
        ("ojk_regulation", "primary_regulation"),
        ("explanation", "explanation"),
        ("attachment_table", "attachment"),
        ("circular", "circular"),
        ("faq", "secondary_faq"),
    ),
)
def test_fixture_document_roles_follow_their_source_family(
    name: str, role: str
) -> None:
    raw_path = FIXTURE_DIR / f"{name}.json"

    assert catalog_raw_record(_fixture(name), raw_path).role == role
