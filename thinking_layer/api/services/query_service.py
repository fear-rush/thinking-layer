from __future__ import annotations

import logging
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from ...answer.composer import build_answer
from ...observability import trace_from_answer


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueryExecution:
    request_id: str
    answer: dict[str, object]
    trace: dict[str, object]
    duration_ms: int


class QueryService:
    """Run the established deterministic answer flow once per API request."""

    def answer(self, question: str) -> QueryExecution:
        request_id = str(uuid4())
        started_at = perf_counter()
        answer = build_answer(
            question,
            max_searches=8,
            limit=12,
            per_document_limit=3,
            max_documents=6,
            max_citations_per_document=3,
        )
        duration_ms = round((perf_counter() - started_at) * 1_000)
        trace = trace_from_answer(answer)
        decision = trace["decision"]
        retrieval = trace["retrieval"]
        logger.info(
            "query_completed request_id=%s status=%s evidence_count=%s duration_ms=%s",
            request_id,
            decision["status"],
            retrieval["evidence_count"],
            duration_ms,
        )
        return QueryExecution(
            request_id=request_id,
            answer=answer,
            trace=trace,
            duration_ms=duration_ms,
        )
