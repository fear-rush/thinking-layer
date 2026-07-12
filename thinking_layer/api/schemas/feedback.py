from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=100)
    helpful: bool
    comment: str | None = Field(default=None, max_length=4_000)


class FeedbackResponse(BaseModel):
    feedback_id: int
    request_id: str
    created_at_utc: datetime
