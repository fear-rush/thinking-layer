from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000, description="Natural-language regulation question.")

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("question must not be blank")
        return normalized


class ConfidenceResponse(BaseModel):
    label: Literal["strong", "partial", "weak", "not_found"]
    score: float
    reasons: list[str]


class CitationResponse(BaseModel):
    id: str
    file_id: str
    block_id: str
    source_block_ids: list[str]
    issuer: str | None = None
    document: str | None = None
    page: int
    page_start: int
    page_end: int
    pasal: str | None = None
    ayat: str | None = None
    huruf: str | None = None
    unit_path: list[str]
    legal_path: dict[str, Any]
    anchors: list[dict[str, Any]]
    source_spans: list[dict[str, Any]]
    text: str | None = None
    excerpt: str | None = None
    assembled_text: str | None = None
    quality: str | None = None


class FindingResponse(BaseModel):
    id: str
    text: str
    citation_ids: list[str]
    kind: Literal["direct_rule", "definition", "scope", "sanction", "other"] = "other"
    status: Literal["supported"] = "supported"


class RelatedDocumentResponse(BaseModel):
    document: str
    issuer: str | None = None
    direct: bool = False


class QueryResponse(BaseModel):
    request_id: str
    status: Literal["answerable", "partial", "not_found"]
    answer: str
    summary: str | None = None
    findings: list[FindingResponse] = Field(default_factory=list)
    related_documents: list[RelatedDocumentResponse] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence: ConfidenceResponse
    citations: list[CitationResponse]
    duration_ms: int = Field(ge=0)
