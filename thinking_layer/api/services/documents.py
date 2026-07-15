from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ...config.paths import SEARCH_INDEX_DB
from ...indexing.sqlite import decode_block_json, sqlite_index_is_current
from ..schemas.documents import DocumentBlockResponse, DocumentResponse


class DocumentStoreUnavailableError(RuntimeError):
    pass


class DocumentNotFoundError(LookupError):
    pass


class DocumentService:
    """Read citation targets from the persisted BM25 index without corpus scans."""

    def __init__(
        self,
        database_path: Path = SEARCH_INDEX_DB,
        index_is_current: Callable[[], bool] = sqlite_index_is_current,
    ) -> None:
        self.database_path = database_path
        self.index_is_current = index_is_current

    def lookup_ready(self) -> bool:
        if not self.database_path.exists() or not self.index_is_current():
            return False
        conn = None
        try:
            conn = sqlite3.connect(self.database_path)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(docs)")}
        except sqlite3.DatabaseError:
            return False
        finally:
            if conn is not None:
                conn.close()
        return {"file_id", "block_id"}.issubset(columns)

    def _connection(self) -> sqlite3.Connection:
        if not self.lookup_ready():
            raise DocumentStoreUnavailableError(
                "Document lookup requires a current SQLite BM25 index. Run `build-index`."
            )
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _block(self, file_id: str, block_id: str | None = None) -> dict[str, Any]:
        conn = self._connection()
        try:
            if block_id is None:
                row = conn.execute(
                    "SELECT block_json FROM docs WHERE file_id = ? ORDER BY page, doc_id LIMIT 1",
                    (file_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT block_json FROM docs WHERE file_id = ? AND block_id = ? LIMIT 1",
                    (file_id, block_id),
                ).fetchone()
        finally:
            conn.close()
        if row is None:
            target = f"block `{block_id}` in " if block_id else ""
            raise DocumentNotFoundError(f"No {target}document found for file_id `{file_id}`.")
        return decode_block_json(row["block_json"])

    def get_document(self, file_id: str) -> DocumentResponse:
        block = self._block(file_id)
        fields = DocumentResponse.model_fields
        return DocumentResponse(**{name: block.get(name) for name in fields})

    def get_block(self, file_id: str, block_id: str) -> DocumentBlockResponse:
        block = self._block(file_id, block_id)
        citation = block.get("citation") or {}
        return DocumentBlockResponse(
            file_id=str(block["file_id"]),
            block_id=str(block["block_id"]),
            document_title=block.get("document_title"),
            issuer=block.get("issuer"),
            page=block.get("page_start"),
            pasal=block.get("pasal"),
            ayat=block.get("ayat"),
            huruf=block.get("huruf"),
            section_type=block.get("section_type"),
            citation_quality=block.get("citation_quality"),
            citation_text=citation.get("text"),
            chunk_schema_version=block.get("chunk_schema_version"),
            node_id=block.get("node_id"),
            parent_id=block.get("parent_id"),
            previous_id=block.get("previous_id"),
            anchors=block.get("anchors"),
            source_spans=block.get("source_spans"),
            source_block_ids=block.get("source_block_ids"),
            unit_path=block.get("unit_path"),
            legal_unit=block.get("legal_unit"),
            legal_path=block.get("legal_path"),
            continuation=block.get("continuation"),
            display_text=block.get("display_text"),
            retrieval_text=block.get("retrieval_text"),
            assembled_text=block.get("assembled_text"),
            text=str(block["display_text"]),
        )
