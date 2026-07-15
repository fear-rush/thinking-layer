from __future__ import annotations

import pytest

from thinking_layer.domain.legal import InstrumentIdentity, SourceDocument


def test_identity_key_includes_issuer_and_instrument_type() -> None:
    bi = InstrumentIdentity("BI", "PBI", "3", 2023)
    ojk = InstrumentIdentity("OJK", "POJK", "3", 2023)

    assert bi.key != ojk.key


def test_source_document_identity_includes_source_specific_material() -> None:
    instrument = InstrumentIdentity("BI", "PBI", "3", 2023)
    first = SourceDocument(
        file_id="bi-pbi-3-2023-primary",
        instrument=instrument,
        title="Peraturan Bank Indonesia Nomor 3 Tahun 2023",
        role="primary_regulation",
        raw_path="processed/raw/liteparse/bi-pbi-3-2023-primary.json",
        source_sha256="a" * 64,
    )
    second = SourceDocument(
        file_id="bi-pbi-3-2023-explanation",
        instrument=instrument,
        title="Penjelasan PBI Nomor 3 Tahun 2023",
        role="explanation",
        raw_path="processed/raw/liteparse/bi-pbi-3-2023-explanation.json",
        source_sha256="b" * 64,
    )

    assert first.identity_key != second.identity_key


def test_rejects_invalid_identity() -> None:
    with pytest.raises(ValueError):
        InstrumentIdentity("", "PBI", "3", 2023)
