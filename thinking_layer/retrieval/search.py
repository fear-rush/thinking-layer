from __future__ import annotations

import argparse
import re
import sqlite3
from typing import Any

from ..config.heuristics import heuristic_section
from ..indexing.lexical import SearchIndex, bm25_search, dedupe_results, filter_index, format_search_results, get_search_index, planned_search
from ..indexing.sqlite import decode_block_json, sqlite_document_candidates, sqlite_index_is_current, sqlite_metadata, sqlite_search, sqlite_title_search
from ..indexing.title import title_search
from ..config.paths import SEARCH_INDEX_DB
from ..common.text import normalize_space
from .planning import build_query_plan, format_query_plan
from .query_tools import load_stopwords, query_overlap_score, tokenize_with_stopwords


def _normalized_anchor(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def row_matches_document_constraints(row: dict[str, Any], constraints: dict[str, str]) -> bool:
    """Match only document-level metadata explicitly stated by the user."""

    if not constraints:
        return True
    regulation_type = constraints.get("regulation_type")
    metadata_text = " ".join(
        str(row.get(key) or "")
        for key in ("regulation_type", "number", "year", "regulation_version_key", "canonical_id", "document_title")
    ).casefold()
    if regulation_type:
        aliases = {
            "PBI": ("pbi", "peraturan bank indonesia"),
            "POJK": ("pojk", "peraturan ojk", "peraturan otoritas jasa keuangan"),
            "PADG": ("padg", "peraturan anggota dewan gubernur"),
            "SEOJK": ("seojk", "surat edaran ojk", "surat edaran otoritas jasa keuangan"),
        }
        if not any(alias in metadata_text for alias in aliases.get(regulation_type, (regulation_type.casefold(),))):
            return False
    if number := constraints.get("regulation_number"):
        row_number = str(row.get("number") or "")
        number_match = re.search(r"\d+", row_number)
        if number_match:
            if number_match.group(0) != number:
                return False
        elif not re.search(rf"(?<!\d){re.escape(number)}(?!\d)", metadata_text):
            return False
    if year := constraints.get("year"):
        row_year = str(row.get("year") or "")
        if row_year and row_year != year:
            return False
        if not row_year and not re.search(rf"(?<!\d){re.escape(year)}(?!\d)", metadata_text):
            return False
    return True


def row_matches_legal_constraints(row: dict[str, Any], constraints: dict[str, str]) -> bool:
    """Require exact requested v2 anchors; another Pasal is never a substitute."""

    if not row_matches_document_constraints(row, constraints):
        return False
    path = row.get("legal_path") or (row.get("citation") or {}).get("legal_path") or {}
    for key in ("pasal", "ayat", "huruf"):
        expected = constraints.get(key)
        if expected and _normalized_anchor(path.get(key) or row.get(key)) != _normalized_anchor(expected):
            return False
    return True


def row_matches_sector_scope(raw_query: str, row: dict[str, Any]) -> bool:
    """Apply explicit/default bank-sector scope before candidate admission."""

    config = heuristic_section("retrieval_ranking", "sector_alignment")
    query_l = raw_query.casefold()
    title_l = str(row.get("document_title") or (row.get("citation") or {}).get("document") or "").casefold()
    bpr_terms = tuple(config.get("bpr_query_terms") or [])
    bank_umum_terms = tuple(config.get("bank_umum_query_terms") or [])
    bpr_query = any(term in query_l for term in bpr_terms)
    bank_umum_query = any(term in query_l for term in bank_umum_terms)
    query_without_central_bank = query_l.replace("bank indonesia", "")
    unqualified_bank_query = bool(re.search(r"(?<!\w)bank(?!\w)", query_without_central_bank))
    if not bpr_query and (bank_umum_query or unqualified_bank_query):
        return not any(term in title_l for term in bpr_terms)
    return True


def discovered_file_ids_for(query: str, title_results: list[dict[str, Any]], constraints: dict[str, str]) -> set[str]:
    rows = [
        row
        for row in title_results
        if row.get("file_id")
        and row_matches_document_constraints(row, constraints)
        and row_matches_sector_scope(query, row)
    ]
    if "penjelasan" not in query.casefold():
        normative = [row for row in rows if "penjelasan" not in str(row.get("file_id") or "").casefold()]
        if normative:
            rows = normative
    return {str(row["file_id"]) for row in rows}


def title_discovery_passage_query(raw_query: str, title_results: list[dict[str, Any]]) -> str:
    """Add bounded abbreviations grounded in shared query/title noun phrases.

    Titles often spell out a regulated object while operative clauses use its
    abbreviation (for example, ``uang kertas asing`` -> ``UKA``).  Only
    contiguous phrases present in both the user query and a discovered title
    may contribute an abbreviation; arbitrary title terms are never injected.
    """

    config = heuristic_section("retrieval_ranking", "title_search")
    min_tokens = int(config.get("discovery_acronym_min_tokens", 3))
    max_tokens = int(config.get("discovery_acronym_max_tokens", 4))
    max_acronyms = int(config.get("max_discovery_acronyms", 4))
    stopwords = load_stopwords()
    query_tokens = tokenize_with_stopwords(raw_query, stopwords)
    query_windows = {
        tuple(query_tokens[index : index + size])
        for size in range(min_tokens, max_tokens + 1)
        for index in range(max(0, len(query_tokens) - size + 1))
    }
    acronyms: list[str] = []
    for row in title_results:
        title_tokens = tokenize_with_stopwords(str(row.get("document_title") or ""), stopwords)
        for size in range(max_tokens, min_tokens - 1, -1):
            for index in range(max(0, len(title_tokens) - size + 1)):
                phrase = tuple(title_tokens[index : index + size])
                if phrase not in query_windows:
                    continue
                acronym = "".join(token[0] for token in phrase if token and token[0].isalpha())
                if len(acronym) >= min_tokens and acronym not in acronyms:
                    acronyms.append(acronym)
                if len(acronyms) >= max_acronyms:
                    return " ".join([raw_query, *acronyms])
    return " ".join([raw_query, *acronyms])


def focused_title_scope(title_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only title candidates close to the best focused-title match."""

    if not title_results:
        return []
    ratio = float(heuristic_section("retrieval_ranking", "title_search").get("scope_min_score_ratio", 0.75))
    best_score = max(float(row.get("_title_score") or 0.0) for row in title_results)
    focused = [row for row in title_results if float(row.get("_title_score") or 0.0) >= best_score * ratio]
    # When a focused title matches both the governing regulation and a
    # subordinate implementation instrument, search the governing POJK/PBI.
    # Explicit type constraints are handled separately before this function.
    governing = [
        row
        for row in focused
        if _normalized_anchor(row.get("regulation_type"))
        in {"peraturan ojk", "pojk", "peraturan bank indonesia", "pbi"}
    ]
    if not governing:
        return focused

    # Do not silently lock an unqualified subject query to only the
    # newest-looking title. Closely named governing regulations can be
    # earlier/later versions with materially different operative clauses.
    best = governing[0]
    best_terms = set(tokenize_with_stopwords(str(best.get("document_title") or ""), load_stopwords()))
    siblings: list[dict[str, Any]] = []
    for row in title_results:
        if _normalized_anchor(row.get("regulation_type")) not in {
            "peraturan ojk", "pojk", "peraturan bank indonesia", "pbi"
        }:
            continue
        terms = set(tokenize_with_stopwords(str(row.get("document_title") or ""), load_stopwords()))
        similarity = len(best_terms & terms) / max(1, len(best_terms | terms))
        if similarity >= 0.70:
            siblings.append(row)
    return list({str(row.get("file_id")): row for row in [*governing, *siblings]}.values())


def focused_scope_quality(raw_query: str, rows: list[dict[str, Any]]) -> tuple[float, float]:
    """Rank document scopes by user-query relevance, then title confidence."""

    return (
        max((query_overlap_score(raw_query, str(row.get("document_title") or "")) for row in rows), default=0.0),
        max((float(row.get("_title_score") or 0.0) for row in rows), default=0.0),
    )


def regulated_subject_multiplier(raw_query: str, row: dict[str, Any], config: dict[str, Any]) -> float:
    """Prefer a clause whose leading subject is the role named by the user."""

    query_l = raw_query.casefold()
    subject_terms = [
        str(term).casefold()
        for term in config.get("regulated_subject_terms") or []
        if re.search(rf"(?<!\w){re.escape(str(term).casefold())}(?!\w)", query_l)
    ]
    if not subject_terms:
        return 1.0
    text = normalize_space(
        str(row.get("assembled_text") or row.get("retrieval_text") or row.get("text") or "")
    ).casefold()
    leading = text[: int(config.get("regulated_subject_leading_chars", 180))]
    if any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", leading) for term in subject_terms):
        return float(config.get("regulated_subject_leading_multiplier", 2.25))
    if any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) for term in subject_terms):
        return float(config.get("regulated_subject_late_multiplier", 0.65))
    return 1.0


def compound_aggregate_multiplier(raw_query: str, row: dict[str, Any], config: dict[str, Any]) -> float:
    if row.get("citation_admission") != "enumeration_aggregate" or " dan " not in raw_query.casefold():
        return 1.0
    return float(config.get("compound_aggregate_multiplier", 2.0))


def query_requests_legal_siblings(query: str) -> bool:
    query_l = query.casefold()
    return (
        " dan kapan " in query_l
        or ("psps" in query_l and "pspk" in query_l)
        or "klausula eksonerasi" in query_l
        or (
            "data" in query_l
            and any(term in query_l for term in ("pihak lain", "perusahaan lain"))
            and any(term in query_l for term in ("pemberian", "memberikan", "membagikan"))
        )
    )


def matching_legal_siblings(seed: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seed_path = seed.get("legal_path") or {}
    seed_file = str(seed.get("file_id") or "")
    seed_pasal = str(seed_path.get("pasal") or seed.get("pasal") or "")
    if not seed_file or not seed_pasal:
        return []
    seed_parent_ayat = str(seed_path.get("ayat") or "") if seed_path.get("huruf") or seed_path.get("angka") else ""
    siblings: list[dict[str, Any]] = []
    for row in candidates:
        path = row.get("legal_path") or {}
        if str(row.get("file_id") or "") != seed_file or str(path.get("pasal") or row.get("pasal") or "") != seed_pasal:
            continue
        if seed_parent_ayat and str(path.get("ayat") or "") != seed_parent_ayat:
            continue
        if row.get("citation_admission") not in {"atomic_leaf", "enumeration_aggregate"}:
            continue
        siblings.append(row)
    return siblings


def enrich_legal_siblings(
    query: str,
    results: list[dict[str, Any]],
    *,
    sqlite_conn: sqlite3.Connection | None = None,
    base_index: SearchIndex | None = None,
) -> list[dict[str, Any]]:
    """Add bounded same-parent units for explicitly compound legal questions."""

    if not query_requests_legal_siblings(query) or not results:
        return []
    enriched: list[dict[str, Any]] = []
    seen_parents: set[tuple[str, str, str]] = set()
    for seed in sorted(results, key=lambda row: float(row.get("_score") or 0.0), reverse=True)[:12]:
        path = seed.get("legal_path") or {}
        parent = (
            str(seed.get("file_id") or ""),
            str(path.get("pasal") or seed.get("pasal") or ""),
            str(path.get("ayat") or "") if path.get("huruf") or path.get("angka") else "",
        )
        if not parent[0] or not parent[1] or parent in seen_parents:
            continue
        seen_parents.add(parent)
        if sqlite_conn is not None:
            rows = sqlite_conn.execute(
                "SELECT block_json FROM docs WHERE file_id = ? AND pasal = ?",
                (parent[0], parent[1]),
            ).fetchall()
            candidates = [decode_block_json(row["block_json"]) for row in rows]
        else:
            candidates = list((base_index or get_search_index(prefer_persisted=True)).blocks)
        for sibling in matching_legal_siblings(seed, candidates):
            row = dict(sibling)
            row["_planned_query"] = query
            row["_plan_reason"] = "legal_sibling"
            row["_bm25_score"] = 0.0
            sibling_text = str(row.get("assembled_text") or row.get("retrieval_text") or row.get("text") or "")
            row["_score"] = (
                float(seed.get("_score") or 0.0) * 0.55
                + query_overlap_score(query, sibling_text) * 8.0
            )
            enriched.append(row)
    return enriched


def dedupe_plan_results(results: list[dict[str, Any]], limit: int, plan: dict[str, Any]) -> list[dict[str, Any]]:
    issuers = list(dict.fromkeys(issuer for issuer in plan.get("issuers") or [] if issuer))
    if len(issuers) < 2:
        return dedupe_results(results, limit)
    candidates = dedupe_results(results, max(limit * 4, limit))
    per_issuer = max(1, limit // len(issuers))
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, str]] = set()
    for issuer in issuers:
        rows = [row for row in candidates if row.get("issuer") == issuer][:per_issuer]
        for row in rows:
            selected.append(row)
            selected_keys.add((str(row.get("file_id") or ""), str(row.get("block_id") or "")))
    for row in candidates:
        key = (str(row.get("file_id") or ""), str(row.get("block_id") or ""))
        if key in selected_keys:
            continue
        selected.append(row)
        if len(selected) >= limit:
            break
    return sorted(selected[:limit], key=lambda row: float(row.get("_score") or 0.0), reverse=True)


def requested_anchor_multiplier(raw_query: str, constraints: dict[str, str], row: dict[str, Any]) -> float:
    if not constraints:
        return 1.0
    if not row_matches_legal_constraints(row, constraints):
        return 0.0
    if not any(constraints.get(key) for key in ("pasal", "ayat", "huruf")):
        if "penjelasan" not in raw_query.casefold() and "penjelasan" in str(row.get("file_id") or "").casefold():
            return 0.45
        return 1.0
    path = row.get("legal_path") or {}
    extra_depth = sum(1 for key in ("pasal", "ayat", "huruf") if path.get(key) and not constraints.get(key))
    multiplier = 1.65 if extra_depth == 0 else max(0.65, 1.25 - (extra_depth * 0.25))
    enumeration_terms = ("apa saja", "sebutkan", "tugas", "kewajiban", "jenis", "persyaratan", "dokumen", "wewenang")
    if row.get("citation_admission") == "enumeration_aggregate" and any(term in raw_query.casefold() for term in enumeration_terms):
        multiplier *= 3.0
    if "penjelasan" not in raw_query.casefold() and "penjelasan" in str(row.get("file_id") or "").casefold():
        multiplier *= 0.45
    return multiplier


def cmd_search(args: argparse.Namespace) -> None:
    if sqlite_index_is_current():
        results = sqlite_search(
            args.query,
            args.limit,
            issuer=args.issuer,
            role=args.role,
            source=args.source,
            include_secondary=args.include_secondary,
        )
    else:
        base_index = get_search_index(prefer_persisted=True)
        index = filter_index(base_index, args.issuer, args.role, args.source, args.include_secondary)
        results = bm25_search(args.query, index, args.limit, issuer=args.issuer) if args.issuer else planned_search(args.query, index, args.limit)
    output = format_search_results(args.query, results)
    print(output)

def execute_query_plan(
    plan: dict[str, Any],
    limit: int,
    index_cache: dict[tuple[Any, Any, Any, bool], SearchIndex] | None = None,
    base_index: SearchIndex | None = None,
) -> list[dict[str, Any]]:
    all_results: list[dict[str, Any]] = []
    constraints = plan.get("legal_constraints") or {}
    requested_pasal = constraints.get("pasal")
    if sqlite_index_is_current():
        conn = sqlite3.connect(SEARCH_INDEX_DB)
        conn.row_factory = sqlite3.Row
        metadata = sqlite_metadata(conn)
        document_candidate_cache: dict[tuple[Any, Any, bool], list[dict[str, Any]]] = {}
        try:
            scoped_file_ids: set[str] | None = None
            plan_issuers = {issuer for issuer in plan.get("issuers") or [] if issuer}
            if not constraints and len(plan_issuers) == 1:
                scope_candidates: list[tuple[tuple[float, float], set[str]]] = []
                primary_topic = str((plan.get("topics") or [""])[0])
                for scope_search in plan["searches"]:
                    scope_reason = str(scope_search.get("reason") or "")
                    if scope_reason.startswith("entity:"):
                        continue
                    if primary_topic and scope_reason.startswith("topic:") and scope_reason != f"topic:{primary_topic}":
                        continue
                    scope_titles = sqlite_title_search(
                        scope_search["query"],
                        max(4, min(limit, 8)),
                        issuer=scope_search.get("issuer"),
                        role=scope_search.get("role"),
                        source=None,
                        include_secondary=bool(scope_search.get("include_secondary", True)),
                        conn=conn,
                    )
                    focused_titles = focused_title_scope(scope_titles)
                    candidate_scope = discovered_file_ids_for(plan["raw_query"], focused_titles, constraints)
                    quality = focused_scope_quality(plan["raw_query"], focused_titles)
                    if candidate_scope:
                        scope_candidates.append((quality, candidate_scope))
                if scope_candidates:
                    best_overlap = max(quality[0] for quality, _ in scope_candidates)
                    eligible = (
                        [candidate for quality, candidate in scope_candidates if quality[0] >= best_overlap * 0.75]
                        if best_overlap > 0
                        else [max(scope_candidates, key=lambda item: item[0])[1]]
                    )
                    scoped_file_ids = set().union(*eligible)
            for search_rank, search in enumerate(plan["searches"], start=1):
                title_results = sqlite_title_search(
                    search["query"],
                    max(4, min(limit, 8)),
                    issuer=search.get("issuer"),
                    role=search.get("role"),
                    source=None,
                    include_secondary=bool(search.get("include_secondary", True)),
                    conn=conn,
                )
                if constraints.get("regulation_number"):
                    document_key = (search.get("issuer"), search.get("role"), bool(search.get("include_secondary", True)))
                    if document_key not in document_candidate_cache:
                        document_candidate_cache[document_key] = sqlite_document_candidates(
                            issuer=search.get("issuer"),
                            role=search.get("role"),
                            source=None,
                            include_secondary=bool(search.get("include_secondary", True)),
                            conn=conn,
                        )
                    title_results = [*title_results, *document_candidate_cache[document_key]]
                discovered_file_ids = discovered_file_ids_for(plan["raw_query"], title_results, constraints)
                if scoped_file_ids is not None:
                    title_results = [row for row in title_results if str(row.get("file_id") or "") in scoped_file_ids]
                    discovered_file_ids &= scoped_file_ids
                discovery_query = title_discovery_passage_query(plan["raw_query"], title_results)
                # A title hit discovers candidate documents.  Its arbitrary
                # representative block is never emitted as answer evidence.
                discovered_results = sqlite_search(
                    discovery_query,
                    max(limit * 4, 16),
                    issuer=search.get("issuer"),
                    role=search.get("role"),
                    source=None,
                    include_secondary=bool(search.get("include_secondary", True)),
                    conn=conn,
                    metadata=metadata,
                    file_ids=discovered_file_ids,
                    pasal=requested_pasal,
                ) if discovered_file_ids else []
                for result_rank, row in enumerate(discovered_results, start=1):
                    if not row_matches_legal_constraints(row, constraints) or not row_matches_sector_scope(plan["raw_query"], row):
                        continue
                    enriched = dict(row)
                    enriched["_planned_query"] = plan["raw_query"]
                    enriched["_plan_reason"] = f"title_discovery:{search['reason']}"
                    enriched["_bm25_score"] = row.get("_score", 0)
                    enriched["_score"] = planned_result_score(
                        plan["raw_query"],
                        {**search, "reason": enriched["_plan_reason"], "legal_constraints": constraints},
                        search_rank,
                        result_rank,
                        row,
                    )
                    all_results.append(enriched)
                candidate_limit = (
                    max(limit * 4, 16)
                    if constraints or str(search.get("reason") or "").startswith("predicate:")
                    else max(limit, 8)
                )
                results = sqlite_search(
                    search["query"],
                    candidate_limit,
                    issuer=search.get("issuer"),
                    role=search.get("role"),
                    source=None,
                    include_secondary=bool(search.get("include_secondary", True)),
                    conn=conn,
                    metadata=metadata,
                    file_ids=scoped_file_ids,
                    pasal=requested_pasal,
                )
                for result_rank, row in enumerate(results, start=1):
                    if not row_matches_legal_constraints(row, constraints) or not row_matches_sector_scope(plan["raw_query"], row):
                        continue
                    enriched = dict(row)
                    enriched["_planned_query"] = search["query"]
                    enriched["_plan_reason"] = search["reason"]
                    enriched["_bm25_score"] = row.get("_score", 0)
                    enriched["_score"] = planned_result_score(
                        plan["raw_query"],
                        {**search, "legal_constraints": constraints},
                        search_rank,
                        result_rank,
                        row,
                    )
                    all_results.append(enriched)
            all_results.extend(enrich_legal_siblings(plan["raw_query"], all_results, sqlite_conn=conn))
        finally:
            conn.close()
        all_results.sort(key=lambda row: row.get("_score", 0), reverse=True)
        return dedupe_plan_results(all_results, limit, plan)

    if index_cache is None:
        index_cache = {}
    if base_index is None:
        base_index = get_search_index(prefer_persisted=True)
    scoped_file_ids: set[str] | None = None
    plan_issuers = {issuer for issuer in plan.get("issuers") or [] if issuer}
    if not constraints and len(plan_issuers) == 1:
        scope_candidates: list[tuple[tuple[float, float], set[str]]] = []
        primary_topic = str((plan.get("topics") or [""])[0])
        for scope_search in plan["searches"]:
            scope_reason = str(scope_search.get("reason") or "")
            if scope_reason.startswith("entity:"):
                continue
            if primary_topic and scope_reason.startswith("topic:") and scope_reason != f"topic:{primary_topic}":
                continue
            key = (scope_search.get("issuer"), scope_search.get("role"), None, bool(scope_search.get("include_secondary", True)))
            if key not in index_cache:
                index_cache[key] = filter_index(
                    base_index,
                    issuer=scope_search.get("issuer"),
                    role=scope_search.get("role"),
                    source=None,
                    include_secondary=bool(scope_search.get("include_secondary", True)),
                )
            scope_titles = title_search(
                scope_search["query"],
                index_cache[key],
                max(4, min(limit, 8)),
                issuer=scope_search.get("issuer"),
                role=scope_search.get("role"),
                source=None,
                include_secondary=bool(scope_search.get("include_secondary", True)),
            )
            focused_titles = focused_title_scope(scope_titles)
            candidate_scope = discovered_file_ids_for(plan["raw_query"], focused_titles, constraints)
            quality = focused_scope_quality(plan["raw_query"], focused_titles)
            if candidate_scope:
                scope_candidates.append((quality, candidate_scope))
        if scope_candidates:
            best_overlap = max(quality[0] for quality, _ in scope_candidates)
            eligible = (
                [candidate for quality, candidate in scope_candidates if quality[0] >= best_overlap * 0.75]
                if best_overlap > 0
                else [max(scope_candidates, key=lambda item: item[0])[1]]
            )
            scoped_file_ids = set().union(*eligible)
    for search_rank, search in enumerate(plan["searches"], start=1):
        key = (search.get("issuer"), search.get("role"), None, bool(search.get("include_secondary", True)))
        if key not in index_cache:
            index_cache[key] = filter_index(
                base_index,
                issuer=search.get("issuer"),
                role=search.get("role"),
                source=None,
                include_secondary=bool(search.get("include_secondary", True)),
            )
        index = index_cache[key]
        title_results = title_search(
            search["query"],
            index,
            max(4, min(limit, 8)),
            issuer=search.get("issuer"),
            role=search.get("role"),
            source=None,
            include_secondary=bool(search.get("include_secondary", True)),
        )
        if constraints.get("regulation_number"):
            title_results = [
                *title_results,
                *(block for block in index.blocks if row_matches_document_constraints(block, constraints)),
            ]
        discovered_file_ids = discovered_file_ids_for(plan["raw_query"], title_results, constraints)
        if scoped_file_ids is not None:
            title_results = [row for row in title_results if str(row.get("file_id") or "") in scoped_file_ids]
            discovered_file_ids &= scoped_file_ids
        discovery_query = title_discovery_passage_query(plan["raw_query"], title_results)
        discovered_results = bm25_search(
            discovery_query,
            index,
            max(limit * 4, 16),
            issuer=search.get("issuer"),
            file_ids=discovered_file_ids,
        ) if discovered_file_ids else []
        for result_rank, row in enumerate(discovered_results, start=1):
            if not row_matches_legal_constraints(row, constraints) or not row_matches_sector_scope(plan["raw_query"], row):
                continue
            enriched = dict(row)
            enriched["_planned_query"] = plan["raw_query"]
            enriched["_plan_reason"] = f"title_discovery:{search['reason']}"
            enriched["_bm25_score"] = row.get("_score", 0)
            enriched["_score"] = planned_result_score(
                plan["raw_query"],
                {**search, "reason": enriched["_plan_reason"], "legal_constraints": constraints},
                search_rank,
                result_rank,
                row,
            )
            all_results.append(enriched)
        candidate_limit = (
            max(limit * 4, 16)
            if constraints or str(search.get("reason") or "").startswith("predicate:")
            else max(limit, 8)
        )
        results = bm25_search(
            search["query"],
            index,
            candidate_limit,
            issuer=search.get("issuer"),
            file_ids=scoped_file_ids,
        )
        for result_rank, row in enumerate(results, start=1):
            if not row_matches_legal_constraints(row, constraints) or not row_matches_sector_scope(plan["raw_query"], row):
                continue
            enriched = dict(row)
            enriched["_planned_query"] = search["query"]
            enriched["_plan_reason"] = search["reason"]
            enriched["_bm25_score"] = row.get("_score", 0)
            enriched["_score"] = planned_result_score(
                plan["raw_query"],
                {**search, "legal_constraints": constraints},
                search_rank,
                result_rank,
                row,
            )
            all_results.append(enriched)

    all_results.extend(enrich_legal_siblings(plan["raw_query"], all_results, base_index=base_index))
    all_results.sort(key=lambda row: row.get("_score", 0), reverse=True)
    return dedupe_plan_results(all_results, limit, plan)

def plan_reason_boost(reason: str) -> float:
    config = heuristic_section("retrieval_ranking", "planned_result").get("reason_boost") or {}
    if reason.startswith(("title:", "title_discovery:")):
        return float(config.get("title", 1.40))
    if reason.startswith("topic:"):
        return float(config.get("topic", 1.25))
    if reason.startswith("intent:"):
        return float(config.get("intent", 1.08))
    if reason.startswith("predicate:"):
        return float(config.get("predicate", 1.80))
    if reason == "legal_alias":
        return float(config.get("legal_alias", 1.65))
    if reason.startswith("entity:"):
        return float(config.get("entity", 1.03))
    return float(config.get("default", 0.90))

def sector_alignment_factor(raw_query: str, title: str) -> float:
    config = heuristic_section("retrieval_ranking", "sector_alignment")
    query_l = raw_query.lower()
    title_l = title.lower()
    bank_umum_query = any(term in query_l for term in config.get("bank_umum_query_terms") or [])
    bpr_query = any(term in query_l for term in config.get("bpr_query_terms") or [])
    # In OJK rules, an unqualified "bank" question follows the Bank Umum
    # branch.  BPR/BPRS rules remain available when the user states that
    # sector explicitly.  Do not interpret "Bank Indonesia" as Bank Umum.
    query_without_central_bank = query_l.replace("bank indonesia", "")
    if not bpr_query and re.search(r"(?<!\w)bank(?!\w)", query_without_central_bank):
        bank_umum_query = True
    bank_umum_title = any(term in title_l for term in config.get("bank_umum_title_terms") or [])
    bpr_title = any(term in title_l for term in config.get("bpr_title_terms") or [])
    if bank_umum_query and bpr_title and not bank_umum_title:
        return float(config.get("bank_umum_query_bpr_title_multiplier", 0.55))
    if bpr_query and bank_umum_title and not bpr_title:
        return float(config.get("bpr_query_bank_umum_title_multiplier", 0.70))
    return 1.0


def lifecycle_multiplier(row: dict[str, Any]) -> float:
    config = heuristic_section("retrieval_ranking", "planned_result")
    status = row.get("lifecycle_status") or "unknown"
    return float((config.get("lifecycle_multiplier") or {}).get(status, 1.0))


def direct_enumeration_aggregate_multiplier(search: dict[str, Any], row: dict[str, Any], config: dict[str, Any]) -> float:
    """Prefer the governing Ayat aggregate for an explicit legal-list question.

    A direct-enumeration plan is only emitted when the question names a legal
    subject and list noun.  Its best answer is the bounded aggregate attached
    to the governing Ayat, not a nested category list or an arbitrary title
    representative.  Atomic children remain separately retrievable and
    citable for follow-up detail.
    """
    if not str(search.get("reason") or "").startswith("direct_enumeration:"):
        return 1.0
    if row.get("citation_admission") != "enumeration_aggregate":
        return 1.0
    path = row.get("legal_path") or {}
    if not path.get("ayat") or path.get("huruf") or path.get("angka"):
        return 1.0
    return float(config.get("direct_enumeration_governing_ayat_multiplier", 5.0))


def planned_result_score(raw_query: str, search: dict[str, Any], search_rank: int, result_rank: int, row: dict[str, Any]) -> float:
    config = heuristic_section("retrieval_ranking", "planned_result")
    constraints = search.get("legal_constraints") or {}
    title = row.get("document_title") or ""
    title_overlap = query_overlap_score(raw_query, title)
    search_overlap = query_overlap_score(raw_query, search.get("query") or "")
    rank_score = float(config.get("rank_score_base", 100.0)) / (result_rank + int(config.get("rank_score_offset", 5)))
    if any(constraints.get(key) for key in ("pasal", "ayat", "huruf")):
        # Once the search is restricted to the requested provision, retain
        # passage-level BM25 magnitude.  Pure inverse rank heavily penalizes a
        # complete aggregate merely because short citation fragments have
        # higher term density.
        rank_score = max(rank_score, min(100.0, float(row.get("_score") or 0.0) * 2.0))
    search_order_decay = 1.0 / (1.0 + max(0, search_rank - 1) * float(config.get("search_order_decay", 0.10)))
    overlap_boost = 1.0 + min(
        float(config.get("overlap_max_boost", 0.60)),
        title_overlap * float(config.get("title_overlap_weight", 0.10)) + search_overlap * float(config.get("search_overlap_weight", 0.04)),
    )
    title_quality = 1.0
    if search["reason"].startswith("title:"):
        title_quality = float(config.get("title_quality_base", 0.70)) + min(
            float(config.get("title_quality_max_bonus", 0.70)),
            float(row.get("_title_score") or 0.0) / float(config.get("title_quality_score_divisor", 160.0)),
        )
    role_multiplier = float((config.get("role_multiplier") or {}).get(row.get("file_role"), 1.0))
    legal_constraint_multiplier = requested_anchor_multiplier(raw_query, constraints, row)
    return (
        rank_score
        * plan_reason_boost(search["reason"])
        * search_order_decay
        * overlap_boost
        * title_quality
        * sector_alignment_factor(raw_query, title)
        * role_multiplier
        * lifecycle_multiplier(row)
        * direct_enumeration_aggregate_multiplier(search, row, config)
        * regulated_subject_multiplier(raw_query, row, config)
        * compound_aggregate_multiplier(raw_query, row, config)
        * legal_constraint_multiplier
    )

def cmd_planned_search(args: argparse.Namespace) -> None:
    plan = build_query_plan(args.query, max_searches=args.max_searches)
    base_index = None if sqlite_index_is_current() else get_search_index(prefer_persisted=True)
    results = execute_query_plan(plan, args.limit, base_index=base_index)
    lines = [format_query_plan(plan), "", format_search_results(args.query, results)]
    print("\n".join(lines))
