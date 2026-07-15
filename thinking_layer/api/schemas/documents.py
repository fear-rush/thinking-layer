from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    file_id: str
    document_title: str | None = None
    issuer: str | None = None
    source: str | None = None
    source_priority: str | None = None
    file_role: str | None = None
    regulation_type: str | None = None
    number: str | None = None
    year: str | None = None
    regulation_version_key: str | None = None
    regulation_series_key: str | None = None
    lifecycle_status: str | None = None
    is_current: bool | None = None


class DocumentBlockResponse(BaseModel):
    file_id: str
    block_id: str
    document_title: str | None = None
    issuer: str | None = None
    page: int | None = None
    pasal: str | None = None
    ayat: str | None = None
    huruf: str | None = None
    section_type: str | None = None
    citation_quality: str | None = None
    citation_text: str | None = None
    node_id: str
    parent_id: str | None = None
    previous_id: str | None = None
    anchors: dict[str, Any] | list[dict[str, Any]]
    source_spans: list[dict[str, Any]]
    source_block_ids: list[str]
    unit_path: list[str]
    legal_unit: dict[str, Any]
    legal_path: dict[str, Any]
    continuation: dict[str, Any] | None = None
    display_text: str
    retrieval_text: str
    assembled_text: str
    text: str
