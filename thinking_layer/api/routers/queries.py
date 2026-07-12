from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_query_service
from ..presenters.queries import present_query
from ..schemas.queries import QueryRequest, QueryResponse
from ..services.query_service import QueryService


router = APIRouter(prefix="/v1", tags=["queries"])


@router.post("/queries", response_model=QueryResponse)
def create_query(
    request: QueryRequest,
    service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    return present_query(service.answer(request.question))
