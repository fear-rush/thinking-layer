from __future__ import annotations

from fastapi import FastAPI

from .routers.documents import router as documents_router
from .routers.feedback import router as feedback_router
from .routers.health import router as health_router
from .routers.queries import router as queries_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Thinking Layer API",
        version="0.1.0",
        description="Citation-first Indonesian financial-regulation retrieval.",
    )
    app.include_router(health_router)
    app.include_router(queries_router)
    app.include_router(documents_router)
    app.include_router(feedback_router)
    return app


app = create_app()
