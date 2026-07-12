from __future__ import annotations

from ...config.paths import SOURCE_CORPUS_PATH
from ...indexing.lexical import persisted_index_exists
from ...indexing.sqlite import sqlite_doc_count, sqlite_index_is_current
from ..schemas.health import HealthResponse
from .documents import DocumentService


class HealthService:
    def __init__(self, document_service: DocumentService | None = None) -> None:
        self.document_service = document_service or DocumentService()

    def status(self) -> HealthResponse:
        sqlite_current = sqlite_index_is_current()
        document_count = None
        if sqlite_current:
            try:
                document_count = sqlite_doc_count()
            except Exception:
                sqlite_current = False
        source_corpus_present = SOURCE_CORPUS_PATH.exists()
        document_lookup_ready = self.document_service.lookup_ready()
        if not document_lookup_ready:
            document_lookup_ready = self.document_service.catalog_ready()
        lexical_index_ready = sqlite_current or persisted_index_exists()
        ready = source_corpus_present and lexical_index_ready and document_lookup_ready
        return HealthResponse(
            status="ok" if ready else "degraded",
            source_corpus_present=source_corpus_present,
            sqlite_index_current=sqlite_current,
            document_lookup_ready=document_lookup_ready,
            lexical_index_ready=lexical_index_ready,
            document_count=document_count,
        )
