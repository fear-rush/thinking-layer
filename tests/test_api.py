from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from thinking_layer.api.app import create_app
from thinking_layer.api.dependencies import (
    get_document_service,
    get_feedback_service,
    get_health_service,
    get_query_service,
)
from thinking_layer.api.schemas.health import HealthResponse
from thinking_layer.api.services.documents import DocumentService
from thinking_layer.api.services.feedback import FeedbackService
from thinking_layer.api.services.query_service import QueryExecution
from thinking_layer.indexing.lexical import build_search_index
from thinking_layer.indexing.sqlite import write_sqlite_search_index


class StubQueryService:
    def answer(self, question: str) -> QueryExecution:
        answer = {
            "status": "answerable",
            "answer": f"Jawaban untuk: {question}",
            "confidence": {"label": "strong", "score": 0.9, "reasons": ["primary evidence"]},
            "citations": [
                {
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
                    "unit_path": ["Pasal 1"],
                    "legal_path": {"pasal": "Pasal 1"},
                    "anchors": [],
                    "source_spans": [],
                    "quality": "document_page_pasal",
                }
            ],
        }
        trace = {"decision": {"status": "answerable"}, "retrieval": {"evidence_count": 1}}
        return QueryExecution(request_id="request-123", answer=answer, trace=trace, duration_ms=12)


class StubHealthService:
    def status(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            source_corpus_present=True,
            sqlite_index_current=True,
            document_lookup_ready=True,
            document_count=1,
        )


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.app.dependency_overrides[get_query_service] = lambda: StubQueryService()
        self.app.dependency_overrides[get_health_service] = lambda: StubHealthService()
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_health_reports_index_readiness(self) -> None:
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertTrue(response.json()["document_lookup_ready"])

    def test_query_returns_stable_answer_and_citation_contract(self) -> None:
        response = self.client.post("/queries", json={"question": "apa aturan PJP?"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["request_id"], "request-123")
        self.assertEqual(body["status"], "answerable")
        self.assertEqual(body["citations"][0]["file_id"], "bi-pjp")
        self.assertEqual(body["citations"][0]["source_block_ids"], ["bi-pjp-1"])
        self.assertEqual(body["citations"][0]["page_start"], 1)
        self.assertEqual(body["citations"][0]["page_end"], 1)
        self.assertNotIn("trace", body)

    def test_query_rejects_empty_question(self) -> None:
        response = self.client.post("/queries", json={"question": ""})

        self.assertEqual(response.status_code, 422)

    def test_query_rejects_blank_question(self) -> None:
        response = self.client.post("/queries", json={"question": "   "})

        self.assertEqual(response.status_code, 422)

    def test_document_and_block_routes_use_indexed_lookup(self) -> None:
        with TemporaryDirectory() as directory:
            service = self._document_service(Path(directory) / "search.sqlite")
            self.app.dependency_overrides[get_document_service] = lambda: service

            document_response = self.client.get("/documents/bi-pjp")
            block_response = self.client.get("/documents/bi-pjp/blocks/bi-pjp-1")

        self.assertEqual(document_response.status_code, 200)
        self.assertEqual(document_response.json()["document_title"], "PBI Penyedia Jasa Pembayaran")
        self.assertEqual(block_response.status_code, 200)
        self.assertEqual(block_response.json()["text"], "Penyedia jasa pembayaran wajib memenuhi ketentuan.")

    def test_document_routes_explain_when_index_needs_rebuild(self) -> None:
        with TemporaryDirectory() as directory:
            directory_path = Path(directory)
            unavailable = DocumentService(
                directory_path / "missing.sqlite",
                index_is_current=lambda: False,
            )
            self.app.dependency_overrides[get_document_service] = lambda: unavailable

            response = self.client.get("/documents/bi-pjp")

        self.assertEqual(response.status_code, 503)
        self.assertIn("build-index", response.json()["detail"])

    def test_feedback_is_persisted_locally(self) -> None:
        with TemporaryDirectory() as directory:
            feedback_path = Path(directory) / "feedback.sqlite"
            self.app.dependency_overrides[get_feedback_service] = lambda: FeedbackService(feedback_path)

            response = self.client.post(
                "/feedback",
                json={"request_id": "request-123", "helpful": True, "comment": "Citation is useful."},
            )
            conn = sqlite3.connect(feedback_path)
            try:
                count = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
            finally:
                conn.close()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["request_id"], "request-123")
        self.assertEqual(count, 1)

    @staticmethod
    def _document_service(database_path: Path) -> DocumentService:
        block = {
            "file_id": "bi-pjp",
            "block_id": "bi-pjp-1",
            "node_id": "bi-pjp-1",
            "document_title": "PBI Penyedia Jasa Pembayaran",
            "issuer": "BI",
            "source": "ease-bi",
            "source_priority": "primary",
            "file_role": "primary_regulation",
            "regulation_type": "PBI",
            "number": "23/6/PBI/2021",
            "year": "2021",
            "regulation_version_key": "bi-pbi-23-6-pbi-2021",
            "regulation_series_key": "bi-pbi-23-6-pbi",
            "lifecycle_status": "current",
            "is_current": True,
            "page_start": 1,
            "page_end": 1,
            "pasal": "Pasal 1",
            "ayat": None,
            "huruf": None,
            "section_type": "pasal",
            "citation_quality": "document_page_pasal",
            "citation": {"text": "PBI Penyedia Jasa Pembayaran, hlm. 1, Pasal 1"},
            "legal_path": {"pasal": "Pasal 1"},
            "unit_path": ["Pasal 1"],
            "anchors": [],
            "source_spans": [],
            "source_block_ids": ["bi-pjp-1"],
            "legal_unit": {"type": "pasal", "legal_path": {"pasal": "Pasal 1"}, "source_spans": []},
            "display_text": "Penyedia jasa pembayaran wajib memenuhi ketentuan.",
            "retrieval_text": "Pasal 1 Penyedia jasa pembayaran wajib memenuhi ketentuan.",
            "assembled_text": "Penyedia jasa pembayaran wajib memenuhi ketentuan.",
            "text": "Penyedia jasa pembayaran wajib memenuhi ketentuan.",
        }
        index = build_search_index([block])
        with (
            patch("thinking_layer.indexing.sqlite.SEARCH_INDEX_DIR", database_path.parent),
            patch("thinking_layer.indexing.sqlite.SEARCH_INDEX_DB", database_path),
        ):
            write_sqlite_search_index(index, filters={})
        return DocumentService(database_path, index_is_current=lambda: True)
