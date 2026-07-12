from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from ...config.paths import API_DOCUMENT_CATALOG_DB, SEARCH_INDEX_DIR


SEARCH_INDEX_DOCS = SEARCH_INDEX_DIR / "docs.ndjson"


def catalog_is_current(
    catalog_path: Path = API_DOCUMENT_CATALOG_DB,
    docs_path: Path = SEARCH_INDEX_DOCS,
) -> bool:
    if not catalog_path.exists() or not docs_path.exists():
        return False
    try:
        conn = sqlite3.connect(catalog_path)
        try:
            metadata = dict(conn.execute("SELECT key, value FROM metadata"))
        finally:
            conn.close()
        return (
            metadata.get("docs_path") == str(docs_path)
            and metadata.get("docs_size") == str(docs_path.stat().st_size)
            and metadata.get("docs_mtime_ns") == str(docs_path.stat().st_mtime_ns)
        )
    except sqlite3.DatabaseError:
        return False


def build_document_catalog(
    catalog_path: Path = API_DOCUMENT_CATALOG_DB,
    docs_path: Path = SEARCH_INDEX_DOCS,
) -> int:
    """Build compact file/block-to-NDJSON-offset lookup data for citation links."""
    if not docs_path.exists():
        raise FileNotFoundError(f"Persisted search docs are missing: {docs_path}")
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    building_path = catalog_path.with_suffix(f"{catalog_path.suffix}.building")
    if building_path.exists():
        building_path.unlink()
    conn = sqlite3.connect(building_path)
    try:
        conn.execute("PRAGMA journal_mode=OFF")
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute(
            "CREATE TABLE blocks (file_id TEXT NOT NULL, block_id TEXT NOT NULL, offset INTEGER NOT NULL, PRIMARY KEY (file_id, block_id)) WITHOUT ROWID"
        )
        rows: list[tuple[str, str, int]] = []
        with docs_path.open("rb") as handle:
            while raw := handle.readline():
                offset = handle.tell() - len(raw)
                if not raw.strip():
                    continue
                block = json.loads(raw)
                file_id = block.get("file_id")
                block_id = block.get("block_id")
                if not file_id or not block_id:
                    continue
                rows.append((str(file_id), str(block_id), offset))
                if len(rows) >= 10_000:
                    conn.executemany("INSERT OR IGNORE INTO blocks (file_id, block_id, offset) VALUES (?, ?, ?)", rows)
                    rows = []
        if rows:
            conn.executemany("INSERT OR IGNORE INTO blocks (file_id, block_id, offset) VALUES (?, ?, ?)", rows)
        conn.execute("CREATE INDEX idx_blocks_file_id ON blocks (file_id)")
        conn.executemany(
            "INSERT INTO metadata (key, value) VALUES (?, ?)",
            [
                ("docs_path", str(docs_path)),
                ("docs_size", str(docs_path.stat().st_size)),
                ("docs_mtime_ns", str(docs_path.stat().st_mtime_ns)),
            ],
        )
        conn.commit()
        count = int(conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0])
    finally:
        conn.close()
    os.replace(building_path, catalog_path)
    return count
