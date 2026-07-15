from __future__ import annotations

import argparse
import json
import re
from typing import Any

from ..config.heuristics import heuristic_section
from ..config.paths import REPORTS_DIR, ROOT
from ..retrieval.evidence import build_evidence_pack, citation_dict
from ..retrieval.query_tools import load_stopwords, tokenize_with_stopwords
from ..common.text import normalize_space, slugify
from .alignment import answer_alignment
from .noise import answer_noise_rank_penalty, should_use_claim_in_answer

def clean_claim_text(text: str, config: dict[str, Any]) -> str:
    cleaned = normalize_space(text)
    for pattern in config.get("strip_regexes") or []:
        replacement = " " if pattern == r"\|[-:\s|]+\|" else ""
        cleaned = re.sub(pattern, replacement, cleaned).strip()
    cleaned = re.sub(r"\s*\|\s*", str(config.get("table_pipe_replacement", "; ")), cleaned).strip(" ;")
    cleaned = re.sub(r"\b([\w-]+)\.{3}\s+\1\b", r"\1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b([A-Za-z]+)-\s+([A-Za-z]+)\b", r"\1-\2", cleaned)
    return normalize_space(cleaned)

def evidence_claim_text(item: dict[str, Any]) -> str:
    config = heuristic_section("answer_ranking", "claim_text")
    # Canonical aggregates and atomic leaves already carry citation-backed assembled
    # text.  Never synthesize a claim from positional neighbors outside the
    # item's source_block_ids graph.
    raw_text = str(item.get("assembled_text") or item.get("text") or item.get("snippet") or "")
    if item.get("section_type") == "enumeration_aggregate":
        # Preserve only actual legal child labels. References such as
        # ``sebagaimana dimaksud dalam huruf i`` occur mid-sentence and must
        # not become new bullets after whitespace normalization.
        raw_text = re.sub(
            r"(?im)(^|[\n:;])\s*huruf\s+([a-z])\s+",
            lambda match: f"{match.group(1)} __LEGAL_HURUF_{match.group(2).lower()}__ ",
            raw_text,
        )
        raw_text = re.sub(
            r"(?im)(^|[\n:;])\s*angka\s+(\d+[a-z]?)\s+",
            lambda match: f"{match.group(1)} __LEGAL_ANGKA_{match.group(2).lower()}__ ",
            raw_text,
        )
    snippet_text = clean_claim_text(raw_text, config)
    if item.get("section_type") == "enumeration_aggregate":
        max_chars = int(config.get("enumeration_aggregate_max_chars", 1600))
    else:
        max_chars = int(config.get("max_chars", 420))
    if len(snippet_text) > max_chars:
        min_boundary_chars = int(config.get("min_boundary_chars", max_chars // 2))
        candidate = snippet_text[:max_chars].rstrip()
        boundary_positions = [
            candidate.rfind(". "),
            candidate.rfind("; "),
            candidate.rfind(": "),
            candidate.rfind(") "),
        ]
        boundary = max(boundary_positions)
        if boundary >= min_boundary_chars:
            snippet_text = candidate[: boundary + 1].rstrip(" ;:")
        else:
            snippet_text = candidate.rstrip(" ;:")
    if snippet_text[:1].islower():
        snippet_text = snippet_text[:1].upper() + snippet_text[1:]
    if item.get("section_type") == "enumeration_aggregate":
        # The canonical unit is already a bounded parent plus its direct children.
        # Render its legal labels as a compact nested list instead of one long
        # paragraph; the text and source graph remain unchanged.
        snippet_text = re.sub(r"\s*__LEGAL_HURUF_([a-z])__\s*", r"\n  - \1. ", snippet_text)
        snippet_text = re.sub(r"\s*__LEGAL_ANGKA_(\d+[a-z]?)__\s*", r"\n  - \1. ", snippet_text)
    if not snippet_text:
        return str(config.get("fallback_claim") or "Ketentuan relevan ditemukan pada sumber yang dikutip.")
    return snippet_text

def is_usable_answer_claim(claim: str, item: dict[str, Any], query: str = "") -> bool:
    config = heuristic_section("answer_ranking", "usable_claim")
    claim_l = claim.lower().strip()
    if not claim_l:
        return False
    if len(claim_l) < int(config.get("min_chars", 0)):
        return False
    if not should_use_claim_in_answer(item, query=query):
        return False
    if config.get("reject_lowercase_start", True) and claim[:1].islower():
        return False
    if claim_l.startswith(tuple(config.get("reject_prefixes") or [])):
        return False
    if any(fragment in claim_l for fragment in config.get("reject_fragments") or []):
        return False
    if any(re.search(str(pattern), claim_l) for pattern in config.get("reject_regexes") or []):
        return False
    all_caps_regex = config.get("all_caps_regex")
    if all_caps_regex and re.match(str(all_caps_regex), claim):
        return False
    section_type = item.get("section_type")
    allowed_terms = (config.get("section_type_query_allow_terms") or {}).get(section_type, [])
    query_allows_section = any(term in query.lower() for term in allowed_terms)
    if section_type in set(config.get("reject_section_types") or []) and not query_allows_section:
        return False
    flag_allow_terms = config.get("extraction_flag_query_allow_terms") or {}
    for flag in item.get("extraction_flags") or []:
        if flag not in set(config.get("reject_extraction_flags") or []):
            continue
        allowed_flag_terms = flag_allow_terms.get(flag, [])
        if not any(term in query.lower() for term in allowed_flag_terms):
            return False
    return True

def query_anchor_score(query: str, item: dict[str, Any], config: dict[str, Any]) -> float:
    anchor_config = config.get("query_anchor") or {}
    generic_terms = set(anchor_config.get("generic_terms") or [])
    min_chars = int(anchor_config.get("min_token_chars", 4))
    key_terms = [
        term
        for term in tokenize_with_stopwords(query, load_stopwords())
        if len(term) >= min_chars and term not in generic_terms
    ]
    if not key_terms:
        return 0.0
    citation = item.get("citation") or {}
    anchor_text = " ".join(
        [
            str(citation.get("document") or ""),
            str(item.get("planned_query") or ""),
            " ".join(str(phrase) for phrase in item.get("matched_exact_phrases") or []),
        ]
    ).lower()
    hits = sum(1 for term in set(key_terms) if term in anchor_text)
    acronym_hits = sum(
        1
        for term in set(key_terms)
        if len(term) <= int(anchor_config.get("acronym_max_chars", 0)) and term in anchor_text
    )
    return min(
        float(anchor_config.get("max_bonus", 0.0)),
        (hits * float(anchor_config.get("per_key_token_bonus", 0.0)))
        + (acronym_hits * float(anchor_config.get("acronym_token_bonus", 0.0))),
    )

def answer_citation_line(citation: dict[str, Any], quality: str | None, section_type: str | None) -> str:
    citation_text = citation.get("text") or citation_dict(citation).get("text")
    details = []
    if quality:
        details.append(f"kualitas {quality}")
    if section_type:
        details.append(f"bagian {section_type}")
    suffix = f" ({'; '.join(details)})" if details else ""
    return f"{citation_text}{suffix}"

def claim_quality_score(query: str, claim: str, config: dict[str, Any]) -> float:
    quality = config.get("claim_quality") or {}
    query_l = query.lower()
    claim_l = claim.lower()
    score = 0.0

    if any(term in query_l for term in quality.get("obligation_query_terms") or []) and any(
        term in claim_l for term in quality.get("obligation_claim_terms") or []
    ):
        score += float(quality.get("obligation_match_bonus", 0.0))

    if any(term in query_l for term in quality.get("definition_query_terms") or []) and any(
        term in claim_l for term in quality.get("definition_claim_terms") or []
    ):
        score += float(quality.get("definition_match_bonus", 0.0))

    for query_term, claim_terms in (quality.get("focus_morphology_matches") or {}).items():
        if str(query_term) not in query_l:
            continue
        if any(str(term) in claim_l for term in claim_terms):
            score += float(quality.get("focus_morphology_bonus", 0.0))
        else:
            score += float(quality.get("focus_morphology_missing_penalty", 0.0))

    for pattern in quality.get("continuation_fragment_patterns") or []:
        if re.search(str(pattern), claim_l):
            score += float(quality.get("continuation_fragment_penalty", 0.0))
            break

    if len(claim_l) <= int(quality.get("short_incomplete_max_chars", 0)) and any(
        claim_l.endswith(str(suffix)) for suffix in quality.get("short_incomplete_suffixes") or []
    ):
        score += float(quality.get("short_incomplete_penalty", 0.0))

    return score


def answer_item_rank(query: str, item: dict[str, Any]) -> float:
    config = heuristic_section("answer_ranking", "item_rank")
    claim = evidence_claim_text(item).lower()
    query_l = query.casefold()
    section_type = item.get("section_type")
    score = float(item.get("support_score") or item.get("score") or 0.0)
    query_terms = set(tokenize_with_stopwords(query, load_stopwords()))
    claim_terms = set(tokenize_with_stopwords(claim, load_stopwords()))
    if query_terms:
        score += float(config.get("query_overlap_weight", 12.0)) * (len(query_terms & claim_terms) / len(query_terms))
    score += len(item.get("matched_exact_phrases") or []) * float(config.get("matched_exact_phrase_bonus", 0.0))
    score += query_anchor_score(query, item, config)
    score += claim_quality_score(query, claim, config)
    sanction_terms = tuple(config.get("sanction_terms") or [])
    if any(term in query.lower() for term in sanction_terms) and any(
        term in claim for term in sanction_terms
    ):
        score += float(config.get("sanction_match_bonus", 10.0))
    permission_seeking = query.strip().casefold().startswith(("bolehkah ", "dapatkah ")) or (
        "data" in query.casefold() and "pihak lain" in query.casefold()
    )
    if permission_seeking and any(
        term in claim
        for term in config.get("permission_answer_terms") or []
    ):
        score += float(config.get("permission_answer_bonus", 24.0))
    for verb in config.get("operative_verbs") or []:
        verb_l = str(verb).casefold()
        if verb_l not in query_l:
            continue
        if re.search(
            rf"\b(?:wajib|harus|dapat|dilarang)\b(?:\s+\w+){{0,3}}\s+{re.escape(verb_l)}\b",
            claim,
        ):
            score += float(config.get("operative_verb_bonus", 35.0))
    score += float((config.get("section_type_bonus") or {}).get(section_type, 0.0))
    score += float((config.get("citation_quality_bonus") or {}).get(item.get("citation_quality"), 0.0))
    regulation_type = normalize_space(str(item.get("regulation_type") or "")).casefold()
    if not any(explicit in query_l for explicit in ("padg", "seojk")):
        if regulation_type in {"pbi", "peraturan bank indonesia", "pojk", "peraturan ojk", "peraturan otoritas jasa keuangan"}:
            score += float(config.get("governing_regulation_bonus", 18.0))
        elif regulation_type in {"padg", "peraturan anggota dewan gubernur", "seojk", "surat edaran ojk"}:
            score += float(config.get("subordinate_instrument_penalty", -12.0))
    score += float((config.get("section_type_penalty") or {}).get(section_type, 0.0))
    score += answer_noise_rank_penalty(item, query=query)
    for prefix, penalty in (config.get("claim_prefix_penalty") or {}).items():
        if claim.startswith(prefix):
            score += float(penalty)
            break
    if not any(term in query.casefold() for term in ("definisi", "pengertian", "yang dimaksud")) and re.match(
        r"^\(?\d+[a-z]?\)?\s+yang dimaksud dengan\b",
        claim,
        flags=re.IGNORECASE,
    ):
        score += float(config.get("unrequested_explanation_penalty", -35.0))
    return score

def row_citation_key(row: tuple[float, str, dict[str, Any], dict[str, Any]]) -> str:
    item = row[3]
    citation = item.get("citation") or {}
    return answer_citation_line(citation, citation.get("quality") or item.get("citation_quality"), item.get("section_type"))


def row_document_key(row: tuple[float, str, dict[str, Any], dict[str, Any]]) -> str:
    item = row[3]
    if item.get("file_id"):
        return f"file:{item['file_id']}"
    title = normalize_space(str(row[2].get("document") or "")).casefold()
    return f"title:{title}"


def row_legal_order_key(row: tuple[float, str, dict[str, Any], dict[str, Any]]) -> tuple[int, int, int]:
    """Order sibling legal units by Ayat, then Huruf, then Angka."""

    path = row[3].get("legal_path") or {}
    ayat_match = re.search(r"\d+", str(path.get("ayat") or ""))
    huruf_match = re.search(r"[a-z]", str(path.get("huruf") or "").casefold())
    angka_match = re.search(r"\d+", str(path.get("angka") or ""))
    return (
        int(ayat_match.group(0)) if ayat_match else 0,
        ord(huruf_match.group(0)) - ord("a") + 1 if huruf_match else 0,
        int(angka_match.group(0)) if angka_match else 0,
    )

def row_has_usable_claim(row: tuple[float, str, dict[str, Any], dict[str, Any]], query: str) -> bool:
    claim = evidence_claim_text(row[3])
    cached_alignment = row[3].get("answer_alignment") or {}
    alignment_accepted = (
        bool(cached_alignment.get("accepted"))
        if "accepted" in cached_alignment
        else answer_alignment(query, row[3]).accepted
    )
    return (
        alignment_accepted
        and is_usable_answer_claim(claim, row[3], query=query)
        and claim_is_complete(claim)
    )


def claim_is_complete(claim: str) -> bool:
    """Reject fragments that would read as an unsupported finding."""

    normalized = normalize_space(claim).rstrip()
    if not normalized:
        return False
    if normalized.endswith((":", ";", "dan/atau")):
        return False
    return not bool(
        re.search(
            r"\b(sebagaimana dimaksud|yang dimaksud|terdiri atas|meliputi|mencakup|berupa|dilakukan melalui)$",
            normalized,
            flags=re.IGNORECASE,
        )
    )


def answer_status_for_pack(pack: dict[str, Any]) -> str:
    confidence = pack.get("confidence") or {}
    if confidence.get("must_say_not_found"):
        return "not_found"
    if confidence.get("label") == "partial":
        return "partial"
    return "answerable"


def source_block_ids_for_item(item: dict[str, Any]) -> list[str]:
    """Return the canonical legal-unit source graph for an assembled claim."""
    raw_ids = item["source_block_ids"]
    return list(dict.fromkeys(str(block_id) for block_id in raw_ids if block_id))


def citation_page_range(item: dict[str, Any], citation: dict[str, Any]) -> tuple[int | None, int | None]:
    page_start = item.get("page_start") or citation.get("page_start") or citation.get("page")
    page_end = item.get("page_end") or citation.get("page_end") or page_start
    return (
        int(page_start) if isinstance(page_start, (int, float)) else None,
        int(page_end) if isinstance(page_end, (int, float)) else None,
    )


def legal_unit_path_for_item(item: dict[str, Any]) -> list[str]:
    raw_path = item["unit_path"]
    return [str(part) for part in raw_path if part]

def compose_template_answer(pack: dict[str, Any], max_documents: int = 6, max_citations_per_document: int = 3) -> dict[str, Any]:
    status = answer_status_for_pack(pack)
    confidence = pack.get("confidence") or {}
    if status == "not_found":
        plan = pack.get("plan") or {}
        ambiguity = plan.get("ambiguity")
        query_l = str(pack.get("query") or "").casefold()
        lifecycle_unknown = "lifecycle_provenance_unavailable" in set(confidence.get("reasons") or [])
        if ambiguity == "institution_type":
            status = "partial"
            summary = "Jawaban masih parsial; perlu memperjelas jenis lembaga keuangan dan regulator yang dimaksud."
        elif ambiguity == "bank_type":
            status = "partial"
            summary = "Jawaban masih parsial; perlu memperjelas jenis bank, seperti Bank Umum, BPR, atau bank syariah."
        elif any(term in query_l for term in ("hitung total", "seluruh nilai numerik", "semua sel tabel")):
            summary = "Tidak dapat menghitung nilai tabel secara andal dari bukti yang tersedia."
        elif lifecycle_unknown:
            summary = "Status keberlakuan tidak dapat dipastikan dari provenance dokumen yang tersedia."
        else:
            summary = "Tidak ditemukan dalam dokumen yang tersedia."
        limitation = (
            "Perlu klarifikasi sebelum memilih ketentuan yang berlaku."
            if ambiguity
            else "Sistem tidak akan menyimpulkan jawaban tanpa dukungan dokumen yang cukup."
        )
        return {
            "query": pack.get("query"),
            "composer": "template",
            "status": status,
            "confidence": confidence,
            "answer": f"{summary}\n\n{limitation}\n",
            "summary": summary,
            "findings": [],
            "related_documents": [],
            "limitations": [limitation],
            "documents_used": [],
            "citation_count": 0,
            "citations": [],
            "policy": pack.get("answer_policy"),
        }

    documents = pack.get("documents") or []
    candidate_items: list[tuple[float, str, dict[str, Any], dict[str, Any]]] = []
    for doc in documents:
        issuer = str(doc.get("issuer") or "UNKNOWN")
        for item in doc.get("citations") or []:
            candidate_items.append((answer_item_rank(str(pack.get("query") or ""), item), issuer, doc, item))

    query = str(pack.get("query") or "")
    query_l = query.casefold()
    legal_constraints = (pack.get("plan") or {}).get("legal_constraints") or {}
    provision_constraints = any(legal_constraints.get(key) for key in ("pasal", "ayat", "huruf"))
    # Broad requests (for example, ``Apa kewajiban ...?``) may legitimately
    # need more than one legal unit.  Narrow yes/no, scalar, and bounded-list
    # questions should lead with the single best unit; adding the adjacent
    # paragraph is usually citation noise rather than useful support.
    max_findings = min(3, max_documents)
    if (
        query_l.startswith(("apakah ", "bolehkah ", "berapa ", "kapan ", "melalui kanal apa ", "melalui apa "))
        or "apa aktivitas inti" in query_l
    ):
        max_findings = 1
    requested_issuers = [issuer for issuer in (pack.get("plan") or {}).get("issuers", []) if issuer]
    multi_rule_query = (
        ("boleh" in query_l and any(term in query_l for term in ("wajib", "harus")))
        or " dan kapan " in query_l
        or ("psps" in query_l and "pspk" in query_l)
        or "klausula eksonerasi" in query_l
    )
    if not provision_constraints and (multi_rule_query or len(set(requested_issuers)) > 1):
        max_findings = min(2, max_documents)
    ranked_items = sorted(candidate_items, key=lambda row: row[0], reverse=True)
    selected_rows: list[tuple[float, str, dict[str, Any], dict[str, Any]]] = []
    seen_row_keys: set[str] = set()
    selected_per_document: dict[str, int] = {}
    plan_issuers = [issuer for issuer in (pack.get("plan") or {}).get("issuers", []) if issuer]
    usable_ranked_items = [row for row in ranked_items if row_has_usable_claim(row, query)]
    strongest_title_overlap = max((float(row[3].get("title_overlap") or 0.0) for row in usable_ranked_items), default=0.0)
    if strongest_title_overlap >= 1.0:
        usable_ranked_items = [
            row for row in usable_ranked_items
            if float(row[3].get("title_overlap") or 0.0) >= strongest_title_overlap * 0.60
        ]
    if multi_rule_query and max_findings >= 2:
        sibling_groups: dict[tuple[str, str, str], list[tuple[float, str, dict[str, Any], dict[str, Any]]]] = {}
        for row in usable_ranked_items:
            item = row[3]
            path = item.get("legal_path") or {}
            pasal = str(path.get("pasal") or "")
            if not pasal:
                continue
            parent = str(path.get("ayat") or "") if path.get("huruf") or path.get("angka") else ""
            key = (str(item.get("file_id") or ""), pasal, parent)
            sibling_groups.setdefault(key, []).append(row)
        complete_groups = [
            sorted(rows, key=lambda row: row[0], reverse=True)[:max_findings]
            for rows in sibling_groups.values()
            if len(rows) >= max_findings
        ]
        if complete_groups:
            sibling_rows = max(complete_groups, key=lambda rows: sum(row[0] for row in rows))
            for row in sibling_rows:
                selected_rows.append(row)
                selected_per_document[row_document_key(row)] = selected_per_document.get(row_document_key(row), 0) + 1
                seen_row_keys.add(row_citation_key(row))
    coverage = pack.get("topic_coverage") or {}
    missing_direct_issuers = set(coverage.get("missing_direct_issuers") or []) if coverage.get("downgrade_required") else set()
    direct_ranked_items: list[tuple[float, str, dict[str, Any], dict[str, Any]]] = []
    if missing_direct_issuers:
        direct_ranked_items = [row for row in ranked_items if row[1] not in missing_direct_issuers]
        direct_usable_ranked_items = [row for row in usable_ranked_items if row[1] not in missing_direct_issuers]
        if direct_usable_ranked_items or direct_ranked_items:
            usable_ranked_items = direct_usable_ranked_items
    for required_issuer in plan_issuers:
        if len(selected_rows) >= max_findings:
            break
        if required_issuer in missing_direct_issuers and (usable_ranked_items or direct_ranked_items):
            continue
        issuer_rows = [row for row in ranked_items if row[1] == required_issuer]
        if issuer_rows:
            selected = next((row for row in issuer_rows if row_has_usable_claim(row, query)), None)
            if selected is not None:
                document_key = row_document_key(selected)
                if selected_per_document.get(document_key, 0) < max_citations_per_document:
                    selected_rows.append(selected)
                    selected_per_document[document_key] = selected_per_document.get(document_key, 0) + 1
                    seen_row_keys.add(row_citation_key(selected))
    for row in usable_ranked_items:
        if len(selected_rows) >= max_findings:
            break
        citation_key = row_citation_key(row)
        if citation_key in seen_row_keys:
            continue
        document_key = row_document_key(row)
        if selected_per_document.get(document_key, 0) >= max_citations_per_document:
            continue
        selected_rows.append(row)
        selected_per_document[document_key] = selected_per_document.get(document_key, 0) + 1
        seen_row_keys.add(citation_key)
        if len(selected_rows) >= max_findings:
            break

    if any(term in query_l for term in ("apa saja", "sebutkan", "daftar", "rincian")) and selected_rows:
        sibling_parents = {
            (
                str(row[3].get("file_id") or ""),
                str((row[3].get("legal_path") or {}).get("pasal") or ""),
            )
            for row in selected_rows
        }
        if len(sibling_parents) == 1 and all(next(iter(sibling_parents))):
            selected_rows.sort(key=row_legal_order_key)

    findings: list[dict[str, Any]] = []
    documents_used_by_title: dict[str, dict[str, Any]] = {}
    citations: list[dict[str, Any]] = []
    seen_citations: set[str] = set()
    citation_count = 0
    source_index = 1
    for _, issuer, doc, item in selected_rows:
        citation = item.get("citation") or {}
        quality = citation.get("quality") or item.get("citation_quality")
        section_type = item.get("section_type")
        citation_key = answer_citation_line(citation, quality, section_type)
        if citation_key in seen_citations:
            continue
        seen_citations.add(citation_key)
        claim = evidence_claim_text(item)
        if not (is_usable_answer_claim(claim, item, query=query) and claim_is_complete(claim)):
            continue
        citation_id = f"c{source_index}"
        page_start, page_end = citation_page_range(item, citation)
        assembled_text = clean_claim_text(
            str(item.get("assembled_text") or item.get("assembled_context") or claim),
            heuristic_section("answer_ranking", "claim_text"),
        )
        citations.append(
            {
                "id": citation_id,
                "file_id": item.get("file_id"),
                "block_id": item.get("block_id"),
                "source_block_ids": source_block_ids_for_item(item),
                "issuer": issuer,
                "document": doc.get("document"),
                "page": page_start,
                "page_start": page_start,
                "page_end": page_end,
                "pasal": citation.get("pasal"),
                "ayat": citation.get("ayat"),
                "huruf": citation.get("huruf"),
                "unit_path": legal_unit_path_for_item(item),
                "legal_path": item.get("legal_path"),
                "anchors": item.get("anchors") or [],
                "source_spans": item.get("source_spans") or [],
                "text": citation.get("text"),
                "excerpt": clean_claim_text(str(item.get("text") or ""), heuristic_section("answer_ranking", "claim_text")),
                "assembled_text": assembled_text,
                "quality": quality,
            }
        )
        findings.append(
            {
                "id": f"f{len(findings) + 1}",
                "text": claim,
                "citation_ids": [citation_id],
                "kind": "direct_rule",
                "status": "supported",
            }
        )
        title = str(doc.get("document") or "")
        if title:
            used_document = documents_used_by_title.setdefault(
                title,
                {
                    "document": doc.get("document"),
                    "issuer": doc.get("issuer"),
                    "source_priority": doc.get("source_priority"),
                    "file_role": doc.get("file_role"),
                    "citations": [],
                },
            )
            if len(used_document["citations"]) < max_citations_per_document:
                used_document["citations"].append({"citation": citation, "snippet": item.get("snippet")})
        citation_count += 1
        source_index += 1
        if citation_count >= max_findings:
            break

    documents_used = list(documents_used_by_title.values())
    related_docs: list[dict[str, Any]] = []
    seen_doc_titles: set[str] = set()
    for doc in documents:
        title = doc.get("document")
        if not title or title in seen_doc_titles or title in documents_used_by_title:
            continue
        seen_doc_titles.add(title)
        related_docs.append({"document": title, "issuer": doc.get("issuer"), "direct": doc.get("issuer") not in missing_direct_issuers})
        if len(related_docs) >= max_documents:
            break

    if not findings:
        status = "not_found"
        confidence = {
            **confidence,
            "label": "weak",
            "must_say_not_found": True,
            "reasons": [*(confidence.get("reasons") or []), "no usable query-aligned answer claim"],
        }
        summary = "Tidak ditemukan dalam dokumen yang tersedia."
        limitations = ["Sistem tidak akan menyimpulkan jawaban tanpa dukungan dokumen yang cukup."]
        related_docs = []
    else:
        ambiguity = (pack.get("plan") or {}).get("ambiguity")
        if ambiguity:
            status = "partial"
        first_document = documents_used[0]["document"]
        summary = f"Ketentuan yang paling relevan ditemukan dalam {first_document}."
        limitations = []
        if ambiguity == "institution_type":
            limitations.append(
                "Jawaban bersifat parsial; perlu memperjelas jenis lembaga keuangan dan regulator yang dimaksud."
            )
        elif ambiguity == "bank_type":
            limitations.append(
                "Jawaban bersifat parsial; perlu memperjelas jenis bank, seperti Bank Umum, BPR, atau bank syariah."
            )
        if status == "partial":
            if not ambiguity:
                limitations.append("Informasi yang ditemukan bersifat parsial dan hanya mencakup ketentuan yang didukung kutipan.")
            if missing_direct_issuers:
                topics = ", ".join(str(value) for value in coverage.get("terms") or []) or "topik yang diminta"
                issuers = ", ".join(sorted(missing_direct_issuers))
                limitations.append(
                    f"Bukti langsung untuk {topics} belum ditemukan pada issuer: {issuers}; "
                    "dokumen tersebut hanya konteks terkait, bukan bukti langsung."
                )
    lines = [summary]
    if findings:
        lines.extend(["", "Temuan:", *[f"- {finding['text']} [{finding['citation_ids'][0]}]" for finding in findings]])
    if limitations:
        lines.extend(["", *limitations])
    return {
        "query": pack.get("query"),
        "composer": "template",
        "status": status,
        "confidence": confidence,
        "answer": "\n".join(lines).rstrip() + "\n",
        "summary": summary,
        "findings": findings,
        "related_documents": related_docs,
        "limitations": limitations,
        "documents_used": documents_used,
        "citation_count": citation_count,
        "citations": citations,
        "policy": pack.get("answer_policy"),
    }

def build_answer(
    query: str,
    max_searches: int,
    limit: int,
    per_document_limit: int,
    max_documents: int,
    max_citations_per_document: int,
) -> dict[str, Any]:
    pack = build_evidence_pack(query, max_searches, limit, per_document_limit)
    answer = compose_template_answer(pack, max_documents=max_documents, max_citations_per_document=max_citations_per_document)
    answer["evidence_pack"] = pack
    return answer

def cmd_answer(args: argparse.Namespace) -> None:
    answer = build_answer(
        args.query,
        max_searches=args.max_searches,
        limit=args.limit,
        per_document_limit=args.per_document_limit,
        max_documents=args.max_documents,
        max_citations_per_document=args.max_citations_per_document,
    )
    print(answer["answer"])
    if args.write_report:
        REPORTS_DIR.mkdir(exist_ok=True)
        stem = slugify(args.query)[:80] or "answer"
        md_path = REPORTS_DIR / f"answer_{stem}.md"
        json_path = REPORTS_DIR / f"answer_{stem}.json"
        md_path.write_text(answer["answer"], encoding="utf-8")
        json_path.write_text(json.dumps(answer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {md_path.relative_to(ROOT)}")
        print(f"Wrote {json_path.relative_to(ROOT)}")
