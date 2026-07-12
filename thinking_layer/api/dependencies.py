from __future__ import annotations

from .services.documents import DocumentService
from .services.feedback import FeedbackService
from .services.health import HealthService
from .services.query_service import QueryService


def get_query_service() -> QueryService:
    return QueryService()


def get_document_service() -> DocumentService:
    return DocumentService()


def get_feedback_service() -> FeedbackService:
    return FeedbackService()


def get_health_service() -> HealthService:
    return HealthService()
