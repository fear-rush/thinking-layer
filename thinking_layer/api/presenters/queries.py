from __future__ import annotations

from ..schemas.queries import CitationResponse, ConfidenceResponse, QueryResponse
from ..services.query_service import QueryExecution


def present_query(execution: QueryExecution) -> QueryResponse:
    answer = execution.answer
    confidence = answer.get("confidence") or {}
    citations = [CitationResponse.model_validate(item) for item in answer.get("citations") or []]
    return QueryResponse(
        request_id=execution.request_id,
        status=answer["status"],
        answer=answer["answer"],
        confidence=ConfidenceResponse(
            label=confidence.get("label") or "not_found",
            score=float(confidence.get("score") or 0.0),
            reasons=list(confidence.get("reasons") or []),
        ),
        citations=citations,
        duration_ms=execution.duration_ms,
    )
