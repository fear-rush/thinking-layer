from __future__ import annotations

from typing import Literal

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
    file_id: str | None = None
    block_id: str | None = None
    issuer: str | None = None
    document: str | None = None
    page: int | None = None
    pasal: str | None = None
    ayat: str | None = None
    huruf: str | None = None
    text: str | None = None
    quality: str | None = None


class QueryResponse(BaseModel):
    request_id: str
    status: Literal["answerable", "partial", "not_found"]
    answer: str
    confidence: ConfidenceResponse
    citations: list[CitationResponse]
    duration_ms: int = Field(ge=0)
