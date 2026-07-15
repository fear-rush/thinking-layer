"""Deterministic API fixture for frontend UI-contract tests only.

It deliberately does not exercise retrieval, generated corpus assets, or the
real QueryService. Live browser acceptance tests start the production API.
"""

from __future__ import annotations

from datetime import datetime, timezone

from thinking_layer.api.app import create_app
from thinking_layer.api.dependencies import (
    get_document_service,
    get_feedback_service,
    get_health_service,
    get_query_service,
)
from thinking_layer.api.schemas.documents import DocumentBlockResponse, DocumentResponse
from thinking_layer.api.schemas.feedback import FeedbackRequest, FeedbackResponse
from thinking_layer.api.schemas.health import HealthResponse
from thinking_layer.api.services.documents import DocumentNotFoundError
from thinking_layer.api.services.query_service import QueryExecution


class BrowserQueryService:
    def answer(self, question: str) -> QueryExecution:
        normalized = question.casefold()
        if "mars" in normalized:
            status = "not_found"
            answer = {
                "status": status,
                "answer": "Tidak ditemukan dalam dokumen yang tersedia.",
                "confidence": {"label": "not_found", "score": 0.0, "reasons": ["no evidence"]},
                "citations": [],
            }
        elif "bandingkan" in normalized:
            status = "partial"
            answer = {
                "status": status,
                "answer": "Bukti langsung tersedia untuk BI, tetapi belum ditemukan untuk OJK.",
                "confidence": {
                    "label": "partial",
                    "score": 0.55,
                    "reasons": ["OJK direct-topic evidence missing"],
                },
                "citations": [_citation()],
            }
        else:
            status = "answerable"
            answer = {
                "status": status,
                "answer": "Penyedia jasa pembayaran wajib memenuhi ketentuan BI.",
                "confidence": {"label": "strong", "score": 0.92, "reasons": ["primary evidence"]},
                "citations": [_citation()],
            }
        return QueryExecution(
            request_id=f"browser-{status}",
            answer=answer,
            trace={
                "decision": {"status": status},
                "retrieval": {"evidence_count": len(answer["citations"])},
            },
            duration_ms=14,
        )


class BrowserDocumentService:
    def get_document(self, file_id: str) -> DocumentResponse:
        if file_id != "bi-pjp":
            raise DocumentNotFoundError(f"No document found for file_id `{file_id}`.")
        return DocumentResponse(
            file_id=file_id,
            document_title="PBI Penyedia Jasa Pembayaran",
            issuer="BI",
            source="browser-test",
            source_priority="primary",
            file_role="primary_regulation",
        )

    def get_block(self, file_id: str, block_id: str) -> DocumentBlockResponse:
        if (file_id, block_id) != ("bi-pjp", "bi-pjp-1"):
            raise DocumentNotFoundError(f"No block `{block_id}` in document `{file_id}`.")
        return DocumentBlockResponse(
            file_id=file_id,
            block_id=block_id,
            document_title="PBI Penyedia Jasa Pembayaran",
            issuer="BI",
            page=1,
            pasal="Pasal 1",
            section_type="pasal",
            citation_quality="document_page_pasal",
            citation_text="PBI Penyedia Jasa Pembayaran, hlm. 1, Pasal 1",
            node_id=block_id,
            anchors={"page_start": 1, "page_end": 1},
            source_spans=[{"block_id": block_id, "page_start": 1, "page_end": 1}],
            source_block_ids=[block_id],
            unit_path=["Pasal 1"],
            legal_unit={"type": "pasal", "legal_path": {"pasal": "Pasal 1"}},
            legal_path={"pasal": "Pasal 1"},
            display_text="Penyedia jasa pembayaran wajib memenuhi ketentuan BI.",
            retrieval_text="Pasal 1 Penyedia jasa pembayaran wajib memenuhi ketentuan BI.",
            assembled_text="Penyedia jasa pembayaran wajib memenuhi ketentuan BI.",
            text="Penyedia jasa pembayaran wajib memenuhi ketentuan BI.",
        )


class BrowserFeedbackService:
    def record(self, feedback: FeedbackRequest) -> FeedbackResponse:
        return FeedbackResponse(
            feedback_id=1,
            request_id=feedback.request_id,
            created_at_utc=datetime.now(timezone.utc),
        )


class BrowserHealthService:
    def status(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            source_corpus_present=True,
            sqlite_index_current=True,
            document_lookup_ready=True,
            document_count=1,
        )


def _citation() -> dict[str, object]:
    return {
        "id": "c1",
        "file_id": "bi-pjp",
        "block_id": "bi-pjp-1",
        "source_block_ids": ["bi-pjp-1"],
        "issuer": "BI",
        "document": "PBI Penyedia Jasa Pembayaran",
        "page": 1,
        "page_start": 1,
        "page_end": 1,
        "pasal": "Pasal 1",
        "ayat": None,
        "huruf": None,
        "unit_path": ["Pasal 1"],
        "legal_path": {"pasal": "Pasal 1"},
        "anchors": [{"page_start": 1, "page_end": 1}],
        "source_spans": [{"block_id": "bi-pjp-1", "page_start": 1, "page_end": 1}],
        "text": "Penyedia jasa pembayaran wajib memenuhi ketentuan BI.",
        "excerpt": "Penyedia jasa pembayaran wajib memenuhi ketentuan BI.",
        "assembled_text": "Penyedia jasa pembayaran wajib memenuhi ketentuan BI.",
        "quality": "document_page_pasal",
    }


app = create_app()
app.dependency_overrides[get_query_service] = BrowserQueryService
app.dependency_overrides[get_document_service] = BrowserDocumentService
app.dependency_overrides[get_feedback_service] = BrowserFeedbackService
app.dependency_overrides[get_health_service] = BrowserHealthService
