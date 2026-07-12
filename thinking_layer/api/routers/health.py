from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_health_service
from ..schemas.health import HealthResponse
from ..services.health import HealthService


router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
def health(service: HealthService = Depends(get_health_service)) -> HealthResponse:
    return service.status()
