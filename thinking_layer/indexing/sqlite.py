from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from typing import Any

from ..config.heuristics import heuristic_section
from ..config.paths import ROOT, SEARCH_INDEX_DB, SEARCH_INDEX_DIR, SOURCE_CORPUS_PATH
from ..retrieval.query_tools import load_stopwords
from .lexical import (
    SearchIndex,
    append_search_index,
    build_search_index,
    index_signature,
    load_persisted_search_index,
    load_search_blocks,
    load_search_blocks_from_offset,
    persisted_index_exists,
    sha1_prefix,
    source_state,
    write_search_index,
)
from .scoring import apply_lexical_boosts, bm25_term_score, candidate_terms_for, query_terms_for, relevant_exact_phrases
from .title import TITLE_SEARCH_MIN_SCORE, document_representative_rank, enrich_title_hit, title_match_score

def write_sqlite_search_index(index: SearchIndex, filters: dict[str, Any], source_state_value: dict[str, Any] | None = None) -> None:
    SEARCH_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    if SEARCH_INDEX_DB.exists():
        SEARCH_INDEX_DB.unlink()
    conn = sqlite3.connect(SEARCH_INDEX_DB)
    try:
        conn.execute("PRAGMA journal_mode=OFF")
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute(
            "CREATE TABLE docs (doc_id INTEGER PRIMARY KEY, issuer TEXT, source TEXT, file_role TEXT, title TEXT, page INTEGER, pasal TEXT, block_json TEXT NOT NULL, doc_len INTEGER NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE document_titles (document_key TEXT PRIMARY KEY, issuer TEXT, source TEXT, file_role TEXT, title TEXT, block_json TEXT NOT NULL)"
        )
        conn.execute("CREATE TABLE doc_terms (doc_id INTEGER NOT NULL, term TEXT NOT NULL, tf INTEGER NOT NULL, PRIMARY KEY (doc_id, term))")
        conn.execute("CREATE TABLE terms (term TEXT PRIMARY KEY, df INTEGER NOT NULL)")
        conn.execute("CREATE TABLE postings (term TEXT NOT NULL, doc_id INTEGER NOT NULL, PRIMARY KEY (term, doc_id))")

        metadata = {
            "signature": index_signature(),
            "source_state": source_state_value or source_state(),
            "filters": filters,
            "doc_count": len(index.blocks),
            "term_count": len(index.doc_freq),
            "avg_len": index.avg_len,
        }
        conn.executemany(
            "INSERT INTO metadata (key, value) VALUES (?, ?)",
            [(key, json.dumps(value, ensure_ascii=False)) for key, value in metadata.items()],
        )
        conn.executemany(
            "INSERT INTO docs (doc_id, issuer, source, file_role, title, page, pasal, block_json, doc_len) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    doc_id,
                    block.get("issuer"),
                    block.get("source"),
                    block.get("file_role"),
                    block.get("document_title"),
                    block.get("page_start"),
                    block.get("pasal"),
                    json.dumps(block, ensure_ascii=False),
                    index.doc_lengths[doc_id],
                )
                for doc_id, block in enumerate(index.blocks)
            ],
        )
        document_representatives: dict[str, dict[str, Any]] = {}
        for block in index.blocks:
            title = block.get("document_title") or ""
            if not title:
                continue
            document_key = "|".join(
                [
                    str(block.get("canonical_id") or ""),
                    str(block.get("file_id") or ""),
                    str(block.get("file_role") or ""),
                    title,
                ]
            )
            current = document_representatives.get(document_key)
            if current is None or document_representative_rank(block) < document_representative_rank(current):
                document_representatives[document_key] = block
        conn.executemany(
            "INSERT INTO document_titles (document_key, issuer, source, file_role, title, block_json) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    key,
                    block.get("issuer"),
                    block.get("source"),
                    block.get("file_role"),
                    block.get("document_title"),
                    json.dumps(block, ensure_ascii=False),
                )
                for key, block in document_representatives.items()
            ],
        )
        term_rows = [(term, int(df)) for term, df in index.doc_freq.items()]
        conn.executemany("INSERT INTO terms (term, df) VALUES (?, ?)", term_rows)

        doc_term_rows = []
        posting_rows = []
        for doc_id, terms in enumerate(index.doc_terms):
            for term, tf in terms.items():
                doc_term_rows.append((doc_id, term, int(tf)))
                posting_rows.append((term, doc_id))
            if len(doc_term_rows) > 100000:
                conn.executemany("INSERT INTO doc_terms (doc_id, term, tf) VALUES (?, ?, ?)", doc_term_rows)
                conn.executemany("INSERT INTO postings (term, doc_id) VALUES (?, ?)", posting_rows)
                doc_term_rows = []
                posting_rows = []
        if doc_term_rows:
            conn.executemany("INSERT INTO doc_terms (doc_id, term, tf) VALUES (?, ?, ?)", doc_term_rows)
            conn.executemany("INSERT INTO postings (term, doc_id) VALUES (?, ?)", posting_rows)

        conn.execute("CREATE INDEX idx_docs_filters ON docs (issuer, file_role, source)")
        conn.execute("CREATE INDEX idx_document_titles_filters ON document_titles (issuer, file_role, source)")
        conn.execute("CREATE INDEX idx_postings_term ON postings (term)")
        conn.execute("CREATE INDEX idx_doc_terms_term_doc ON doc_terms (term, doc_id)")
        conn.commit()
    finally:
        conn.close()

def sqlite_index_exists() -> bool:
    return SEARCH_INDEX_DB.exists()


def sqlite_index_is_current() -> bool:
    if not sqlite_index_exists():
        return False
    conn = sqlite3.connect(SEARCH_INDEX_DB)
    try:
        metadata = sqlite_metadata(conn)
    except sqlite3.DatabaseError:
        return False
    finally:
        conn.close()
    return metadata.get("signature") == index_signature()

def sqlite_metadata(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT key, value FROM metadata").fetchall()
    return {key: json.loads(value) for key, value in rows}

def sqlite_doc_count() -> int:
    conn = sqlite3.connect(SEARCH_INDEX_DB)
    try:
        return int(sqlite_metadata(conn).get("doc_count") or 0)
    finally:
        conn.close()

def sqlite_has_table(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return bool(row)

def sqlite_title_search(
    query: str,
    limit: int,
    issuer: str | None = None,
    role: str | None = None,
    source: str | None = None,
    include_secondary: bool = True,
    conn: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    if not sqlite_index_exists():
        return []

    owns_conn = conn is None
    if conn is None:
        conn = sqlite3.connect(SEARCH_INDEX_DB)
        conn.row_factory = sqlite3.Row
    try:
        if not sqlite_has_table(conn, "document_titles"):
            return []
        filters = []
        params: list[Any] = []
        if issuer:
            filters.append("issuer = ?")
            params.append(issuer)
        if role:
            filters.append("file_role = ?")
            params.append(role)
        if source:
            filters.append("source = ?")
            params.append(source)
        if not include_secondary:
            filters.append("file_role NOT IN ('secondary_faq', 'secondary_summary')")
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = conn.execute(
            f"SELECT title, block_json FROM document_titles {where}",
            params,
        ).fetchall()
        stopwords = load_stopwords()
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            score = title_match_score(query, row["title"] or "", stopwords)
            if score < TITLE_SEARCH_MIN_SCORE:
                continue
            block = json.loads(row["block_json"])
            scored.append((score, enrich_title_hit(block, score, query)))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [row for _, row in scored[:limit]]
    finally:
        if owns_conn:
            conn.close()

def sqlite_search(
    query: str,
    limit: int,
    issuer: str | None = None,
    role: str | None = None,
    source: str | None = None,
    include_secondary: bool = True,
    conn: sqlite3.Connection | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not sqlite_index_exists():
        return []

    stopwords = load_stopwords()
    query_terms = query_terms_for(query, stopwords)
    if not query_terms:
        return []
    query_counter = Counter(query_terms)
    exact_phrases = relevant_exact_phrases(query)

    owns_conn = conn is None
    if conn is None:
        conn = sqlite3.connect(SEARCH_INDEX_DB)
        conn.row_factory = sqlite3.Row
    try:
        if metadata is None:
            metadata = sqlite_metadata(conn)
        doc_count = int(metadata.get("doc_count") or 0)
        avg_len = float(metadata.get("avg_len") or 1.0)

        term_placeholders = ",".join("?" for _ in set(query_terms))
        df_rows = conn.execute(
            f"SELECT term, df FROM terms WHERE term IN ({term_placeholders})",
            list(set(query_terms)),
        ).fetchall()
        doc_freq = {row["term"]: row["df"] for row in df_rows}
        candidate_config = heuristic_section("retrieval_ranking", "candidate_selection")
        candidate_terms = candidate_terms_for(query_terms, doc_freq)
        if not candidate_terms:
            return []

        placeholders = ",".join("?" for _ in candidate_terms)
        min_match = (
            int(candidate_config.get("sqlite_min_match", 2))
            if len(candidate_terms) >= int(candidate_config.get("sqlite_min_match_when_candidate_terms_at_least", 3))
            else int(candidate_config.get("sqlite_default_min_match", 1))
        )
        candidate_rows = conn.execute(
            f"""
            SELECT doc_id, COUNT(DISTINCT term) AS matched_terms
            FROM postings
            WHERE term IN ({placeholders})
            GROUP BY doc_id
            HAVING matched_terms >= ?
            ORDER BY matched_terms DESC
            LIMIT {int(candidate_config.get("sqlite_candidate_limit", 50000))}
            """,
            [*candidate_terms, min_match],
        ).fetchall()
        candidate_ids = [row["doc_id"] for row in candidate_rows]
        if not candidate_ids:
            return []

        filters = []
        params: list[Any] = []
        if issuer:
            filters.append("issuer = ?")
            params.append(issuer)
        if role:
            filters.append("file_role = ?")
            params.append(role)
        if source:
            filters.append("source = ?")
            params.append(source)
        if not include_secondary:
            filters.append("file_role NOT IN ('secondary_faq', 'secondary_summary')")

        scored: list[tuple[float, dict[str, Any]]] = []
        batch_size = int(candidate_config.get("sqlite_batch_size", 900))
        for offset in range(0, len(candidate_ids), batch_size):
            batch = candidate_ids[offset : offset + batch_size]
            doc_placeholders = ",".join("?" for _ in batch)
            where = [f"doc_id IN ({doc_placeholders})", *filters]
            doc_rows = conn.execute(
                f"SELECT * FROM docs WHERE {' AND '.join(where)}",
                [*batch, *params],
            ).fetchall()
            if not doc_rows:
                continue
            doc_ids = [row["doc_id"] for row in doc_rows]
            doc_id_set = set(doc_ids)
            tf_rows = conn.execute(
                f"SELECT doc_id, term, tf FROM doc_terms WHERE doc_id IN ({','.join('?' for _ in doc_ids)}) AND term IN ({term_placeholders})",
                [*doc_ids, *set(query_terms)],
            ).fetchall()
            term_map: dict[int, dict[str, int]] = defaultdict(dict)
            for row in tf_rows:
                if row["doc_id"] in doc_id_set:
                    term_map[row["doc_id"]][row["term"]] = row["tf"]

            for row in doc_rows:
                doc_id = row["doc_id"]
                terms = term_map.get(doc_id, {})
                if not terms:
                    continue
                doc_len = row["doc_len"] or 1
                score = bm25_term_score(query_counter, terms, doc_freq, doc_count, doc_len, avg_len)
                if score <= 0:
                    continue

                block = json.loads(row["block_json"])
                score, matched_phrases = apply_lexical_boosts(score, query, query_terms, stopwords, block, exact_phrases)
                if matched_phrases:
                    block["_matched_exact_phrases"] = matched_phrases
                block["_score"] = score
                scored.append((score, block))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [row for _, row in scored[:limit]]
    finally:
        if owns_conn:
            conn.close()

def incremental_build_index(filters: dict[str, Any]) -> tuple[bool, str]:
    if not sqlite_index_exists() or not persisted_index_exists() or not SOURCE_CORPUS_PATH.exists():
        return False, "an existing SQLite/JSON index and source corpus are required"
    conn = sqlite3.connect(SEARCH_INDEX_DB)
    try:
        metadata = sqlite_metadata(conn)
    finally:
        conn.close()
    previous = metadata.get("source_state") or {}
    current_signature = index_signature()
    if not previous and metadata.get("signature") == current_signature:
        source_state_value = source_state()
        json_metadata_path = SEARCH_INDEX_DIR / "metadata.json"
        json_metadata = json.loads(json_metadata_path.read_text(encoding="utf-8"))
        json_metadata["source_state"] = source_state_value
        json_metadata_path.write_text(json.dumps(json_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        conn = sqlite3.connect(SEARCH_INDEX_DB)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                ("source_state", json.dumps(source_state_value, ensure_ascii=False)),
            )
            conn.commit()
        finally:
            conn.close()
        return True, "initialized append-only source state; index was already current"
    current_path = str(SOURCE_CORPUS_PATH.relative_to(ROOT))
    previous_path = previous.get("path")
    previous_size = previous.get("size")
    if previous_path != current_path or not isinstance(previous_size, int):
        return False, "the index has no compatible append-only source state"
    current_size = SOURCE_CORPUS_PATH.stat().st_size
    if current_size < previous_size:
        return False, "the source corpus shrank"
    if previous.get("prefix_sha1") != sha1_prefix(SOURCE_CORPUS_PATH, previous_size):
        return False, "existing source-corpus bytes changed; a full rebuild is required"
    new_blocks = load_search_blocks_from_offset(previous_size, None, None, None, True)
    source_state_value = source_state()
    if not new_blocks and current_size == previous_size and metadata.get("signature") == current_signature:
        return True, "index is already current"
    index = load_persisted_search_index()
    append_search_index(index, new_blocks)
    write_search_index(index, filters, source_state_value=source_state_value)
    write_sqlite_search_index(index, filters, source_state_value=source_state_value)
    return True, f"appended {len(new_blocks)} new searchable blocks"


def cmd_build_index(args: argparse.Namespace) -> None:
    filters = {
        "issuer": None,
        "role": None,
        "source": None,
        "include_secondary": True,
        "extracted_ok_only": True,
        "corpus": str(SOURCE_CORPUS_PATH.relative_to(ROOT)) if SOURCE_CORPUS_PATH.exists() else "processed/blocks.ndjson",
    }
    if args.incremental:
        updated, message = incremental_build_index(filters)
        if updated:
            print(f"Incremental index update: {message}", flush=True)
            return
        print(f"Incremental update unavailable: {message}; performing full rebuild.", flush=True)
    blocks = load_search_blocks(None, None, None, include_secondary=True)
    if args.limit:
        blocks = blocks[: args.limit]
    print(f"Building search index for {len(blocks)} blocks...", flush=True)
    index = build_search_index(blocks)
    source_state_value = source_state()
    write_search_index(index, filters, source_state_value=source_state_value)
    write_sqlite_search_index(index, filters, source_state_value=source_state_value)
    print(f"Wrote {SEARCH_INDEX_DIR.relative_to(ROOT)}/metadata.json")
    print(f"Wrote {SEARCH_INDEX_DIR.relative_to(ROOT)}/docs.ndjson")
    print(f"Wrote {SEARCH_INDEX_DIR.relative_to(ROOT)}/terms.ndjson")
    print(f"Wrote {SEARCH_INDEX_DIR.relative_to(ROOT)}/postings.ndjson")
    print(f"Wrote {SEARCH_INDEX_DB.relative_to(ROOT)}")
