from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    source_corpus_present: bool
    sqlite_index_current: bool
    document_lookup_ready: bool
    lexical_index_ready: bool = False
    document_count: int | None = None
