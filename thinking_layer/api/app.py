from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse


def create_app() -> FastAPI:
    app = FastAPI(
        title="Thinking Layer API",
        version="0.0.0-migration",
        description="The legacy retrieval API has been removed during the hard cutover.",
    )

    @app.get("/healthz")
    def health() -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "status": "migration_in_progress",
                "detail": "The retrieval API will return when the new corpus and database contract is implemented.",
            },
        )

    return app


app = create_app()
