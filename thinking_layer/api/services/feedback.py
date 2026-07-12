from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ...config.paths import API_FEEDBACK_DB
from ..schemas.feedback import FeedbackRequest, FeedbackResponse


class FeedbackService:
    def __init__(self, database_path: Path = API_FEEDBACK_DB) -> None:
        self.database_path = database_path

    def _initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.database_path)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, request_id TEXT NOT NULL, helpful INTEGER NOT NULL, comment TEXT, created_at_utc TEXT NOT NULL)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_request_id ON feedback (request_id)")
            conn.commit()
        finally:
            conn.close()

    def record(self, feedback: FeedbackRequest) -> FeedbackResponse:
        self._initialize()
        created_at = datetime.now(timezone.utc)
        conn = sqlite3.connect(self.database_path)
        try:
            cursor = conn.execute(
                "INSERT INTO feedback (request_id, helpful, comment, created_at_utc) VALUES (?, ?, ?, ?)",
                (feedback.request_id, int(feedback.helpful), feedback.comment, created_at.isoformat()),
            )
            feedback_id = int(cursor.lastrowid)
            conn.commit()
        finally:
            conn.close()
        return FeedbackResponse(feedback_id=feedback_id, request_id=feedback.request_id, created_at_utc=created_at)
