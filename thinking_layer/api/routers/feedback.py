from __future__ import annotations

from fastapi import APIRouter, Depends, status

from ..dependencies import get_feedback_service
from ..schemas.feedback import FeedbackRequest, FeedbackResponse
from ..services.feedback import FeedbackService


router = APIRouter(prefix="/v1", tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    request: FeedbackRequest,
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse:
    return service.record(request)
