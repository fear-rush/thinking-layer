from __future__ import annotations

from typing import Any

from ..schemas.queries import CitationResponse, ConfidenceResponse, FindingResponse, QueryResponse, RelatedDocumentResponse
from ..services.query_service import QueryExecution


def present_citation(item: dict[str, Any]) -> CitationResponse:
    """Validate the canonical citation payload at the API boundary."""
    return CitationResponse.model_validate(item)


def present_query(execution: QueryExecution) -> QueryResponse:
    answer = execution.answer
    confidence = answer.get("confidence") or {}
    citations = [present_citation(item) for item in answer.get("citations") or []]
    return QueryResponse(
        request_id=execution.request_id,
        status=answer["status"],
        answer=answer["answer"],
        summary=answer.get("summary"),
        findings=[FindingResponse.model_validate(item) for item in answer.get("findings") or []],
        related_documents=[RelatedDocumentResponse.model_validate(item) for item in answer.get("related_documents") or []],
        limitations=list(answer.get("limitations") or []),
        confidence=ConfidenceResponse(
            label=confidence.get("label") or "not_found",
            score=float(confidence.get("score") or 0.0),
            reasons=list(confidence.get("reasons") or []),
        ),
        citations=citations,
        duration_ms=execution.duration_ms,
    )
