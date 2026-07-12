from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from functools import lru_cache
from typing import Any

from ..config.heuristics import heuristic_section
from ..config.paths import REPORTS_DIR, ROOT, SOURCE_CORPUS_PATH
from ..common.io import iter_ndjson_file
from ..retrieval.evidence import build_evidence_pack, citation_dict
from ..retrieval.query_tools import load_stopwords, tokenize_with_stopwords
from ..common.text import normalize_space, slugify
from .noise import answer_noise_rank_penalty, should_use_claim_in_answer

def clean_claim_text(text: str, config: dict[str, Any]) -> str:
    cleaned = normalize_space(text)
    for pattern in config.get("strip_regexes") or []:
        replacement = " " if pattern == r"\|[-:\s|]+\|" else ""
        cleaned = re.sub(pattern, replacement, cleaned).strip()
    cleaned = re.sub(r"\s*\|\s*", str(config.get("table_pipe_replacement", "; ")), cleaned).strip(" ;")
    return normalize_space(cleaned)

@lru_cache(maxsize=1)
def source_context_index() -> dict[str, Any]:
    by_key: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    positions: dict[str, list[tuple[tuple[Any, Any, Any], int]]] = defaultdict(list)
    for row in iter_ndjson_file(SOURCE_CORPUS_PATH) or []:
        file_id = row.get("file_id")
        block_id = row.get("block_id")
        if not file_id or not block_id:
            continue
        context_row = {
            "block_id": block_id,
            "block_type": row.get("block_type"),
            "section_type": row.get("section_type"),
            "text": row.get("text") or "",
        }
        key = (file_id, row.get("page_start"), row.get("pasal"))
        positions[str(block_id)].append((key, len(by_key[key])))
        by_key[key].append(context_row)
    return {"by_key": by_key, "positions": positions}

def claim_needs_context_expansion(claim: str, config: dict[str, Any]) -> bool:
    claim_l = claim.lower().rstrip()
    return any(claim_l.endswith(str(suffix).lower()) for suffix in config.get("context_expansion_suffixes") or [])

def join_context_fragments(claim: str, fragments: list[str]) -> str:
    text = claim
    for fragment in fragments:
        previous = text.rstrip()
        if previous.lower().endswith((" dan", "; dan", " atau", "; atau", " dan/atau", "; dan/atau")):
            separator = " "
        elif previous.endswith(":"):
            separator = " "
        else:
            separator = "; "
        text = f"{previous}{separator}{fragment}"
    return normalize_space(text)

def expand_claim_with_neighbor_context(claim: str, item: dict[str, Any], config: dict[str, Any]) -> str:
    if not claim_needs_context_expansion(claim, config):
        return claim
    block_id = item.get("block_id")
    if not block_id:
        return claim
    index = source_context_index()
    positions = index["positions"].get(str(block_id)) or []
    if not positions:
        return claim
    expected_key = (item.get("file_id"), item.get("page_start"), item.get("pasal"))
    matching_positions = [position for position in positions if position[0] == expected_key] or positions
    key, row_index = matching_positions[0]
    item_text = clean_claim_text(str(item.get("text") or item.get("snippet") or ""), config).lower()
    for candidate_key, candidate_index in matching_positions:
        candidate_rows = index["by_key"].get(candidate_key) or []
        if candidate_index >= len(candidate_rows):
            continue
        candidate_text = clean_claim_text(str(candidate_rows[candidate_index].get("text") or ""), config).lower()
        if candidate_text == item_text or item_text in candidate_text or candidate_text in item_text:
            key, row_index = candidate_key, candidate_index
            break
    rows = index["by_key"].get(key) or []
    allowed_types = set(config.get("context_expansion_block_types") or [])
    max_blocks = int(config.get("context_expansion_max_blocks", 0))
    max_context_chars = int(config.get("context_expansion_max_chars", 0))
    parts: list[str] = []
    context_chars = 0
    for row in rows[row_index + 1 :]:
        row_type = row.get("block_type") or row.get("section_type")
        section_type = row.get("section_type")
        if allowed_types and row_type not in allowed_types and section_type not in allowed_types:
            break
        fragment = clean_claim_text(str(row.get("text") or ""), config)
        if not fragment:
            continue
        if max_context_chars and context_chars + len(fragment) > max_context_chars:
            remaining = max_context_chars - context_chars
            if remaining <= 0:
                break
            fragment = fragment[:remaining].rstrip(" ;:")
        parts.append(fragment)
        context_chars += len(fragment)
        if max_blocks and len(parts) >= max_blocks:
            break
        if max_context_chars and context_chars >= max_context_chars:
            break
    if not parts:
        return claim
    return join_context_fragments(claim, parts)

def evidence_claim_text(item: dict[str, Any]) -> str:
    config = heuristic_section("answer_ranking", "claim_text")
    snippet_text = clean_claim_text(str(item.get("text") or item.get("snippet") or ""), config)
    snippet_text = expand_claim_with_neighbor_context(snippet_text, item, config)
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
    score += float((config.get("section_type_bonus") or {}).get(section_type, 0.0))
    score += float((config.get("citation_quality_bonus") or {}).get(item.get("citation_quality"), 0.0))
    score += float((config.get("section_type_penalty") or {}).get(section_type, 0.0))
    score += answer_noise_rank_penalty(item, query=query)
    for prefix, penalty in (config.get("claim_prefix_penalty") or {}).items():
        if claim.startswith(prefix):
            score += float(penalty)
            break
    return score

def row_citation_key(row: tuple[float, str, dict[str, Any], dict[str, Any]]) -> str:
    item = row[3]
    citation = item.get("citation") or {}
    return answer_citation_line(citation, citation.get("quality") or item.get("citation_quality"), item.get("section_type"))

def row_has_usable_claim(row: tuple[float, str, dict[str, Any], dict[str, Any]], query: str) -> bool:
    return is_usable_answer_claim(evidence_claim_text(row[3]), row[3], query=query)

def answer_status_for_pack(pack: dict[str, Any]) -> str:
    confidence = pack.get("confidence") or {}
    if confidence.get("must_say_not_found"):
        return "not_found"
    if confidence.get("label") == "partial":
        return "partial"
    return "answerable"

def compose_template_answer(pack: dict[str, Any], max_documents: int = 6, max_citations_per_document: int = 2) -> dict[str, Any]:
    status = answer_status_for_pack(pack)
    confidence = pack.get("confidence") or {}
    if status == "not_found":
        text = "\n".join(
            [
                "Tidak ditemukan dalam dokumen yang tersedia.",
                "",
                f"Alasan: evidence confidence `{confidence.get('label')}` dengan skor `{confidence.get('score')}`. Sistem tidak akan menyimpulkan jawaban tanpa dukungan dokumen yang cukup.",
            ]
        )
        return {
            "query": pack.get("query"),
            "composer": "template",
            "status": status,
            "confidence": confidence,
            "answer": text,
            "documents_used": [],
            "citation_count": 0,
            "citations": [],
            "policy": pack.get("answer_policy"),
        }

    documents = (pack.get("documents") or [])[:max_documents]
    docs_by_issuer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for doc in documents:
        docs_by_issuer[str(doc.get("issuer") or "UNKNOWN")].append(doc)

    lines = [
        "Jawaban berbasis dokumen:",
        f"Status evidence: `{confidence.get('label')}` dengan skor `{confidence.get('score')}`.",
        "",
    ]
    if status == "partial":
        lines.extend(
            [
                "Catatan: evidence bersifat parsial. Saya hanya menyatakan hal yang muncul pada dokumen terambil; detail yang tidak dikutip dianggap tidak ditemukan dalam korpus saat ini.",
                "",
            ]
        )
        coverage = pack.get("topic_coverage") or {}
        if coverage.get("downgrade_required"):
            missing = ", ".join(coverage.get("missing_direct_issuers") or [])
            terms = ", ".join(coverage.get("terms") or [])
            lines.extend(
                [
                    f"Catatan cakupan regulator: evidence langsung untuk topik `{terms}` belum ditemukan pada issuer: {missing}. Evidence yang hanya menyebut topik secara insidental tidak diperlakukan sebagai dasar langsung.",
                    "",
                ]
            )

    documents_used: list[dict[str, Any]] = []
    citation_count = 0
    candidate_items: list[tuple[float, str, dict[str, Any], dict[str, Any]]] = []
    for issuer in sorted(docs_by_issuer):
        for doc_index, doc in enumerate(docs_by_issuer[issuer], start=1):
            used_citations = []
            for item in (doc.get("citations") or [])[:max_citations_per_document]:
                citation = item.get("citation") or {}
                quality = citation.get("quality") or item.get("citation_quality")
                section_type = item.get("section_type")
                candidate_items.append((answer_item_rank(str(pack.get("query") or ""), item), issuer, doc, item))
                used_citations.append(
                    {
                        "citation": citation,
                        "section_type": section_type,
                        "citation_quality": quality,
                        "snippet": item.get("snippet"),
                    }
                )
            documents_used.append(
                {
                    "document": doc.get("document"),
                    "issuer": doc.get("issuer"),
                    "source_priority": doc.get("source_priority"),
                    "file_role": doc.get("file_role"),
                    "citations": used_citations,
                }
            )

    query = str(pack.get("query") or "")
    ranked_items = sorted(candidate_items, key=lambda row: row[0], reverse=True)
    selected_rows: list[tuple[float, str, dict[str, Any], dict[str, Any]]] = []
    seen_row_keys: set[str] = set()
    plan_issuers = [issuer for issuer in (pack.get("plan") or {}).get("issuers", []) if issuer]
    usable_ranked_items = [row for row in ranked_items if row_has_usable_claim(row, query)]
    fallback_ranked_items = [row for row in ranked_items if not row_has_usable_claim(row, query)]
    coverage = pack.get("topic_coverage") or {}
    missing_direct_issuers = set(coverage.get("missing_direct_issuers") or []) if coverage.get("downgrade_required") else set()
    direct_ranked_items: list[tuple[float, str, dict[str, Any], dict[str, Any]]] = []
    if missing_direct_issuers:
        direct_ranked_items = [row for row in ranked_items if row[1] not in missing_direct_issuers]
        direct_usable_ranked_items = [row for row in usable_ranked_items if row[1] not in missing_direct_issuers]
        if direct_usable_ranked_items or direct_ranked_items:
            usable_ranked_items = direct_usable_ranked_items
            fallback_ranked_items = [row for row in fallback_ranked_items if row[1] not in missing_direct_issuers]
    for required_issuer in plan_issuers:
        if required_issuer in missing_direct_issuers and (usable_ranked_items or direct_ranked_items):
            continue
        issuer_rows = [row for row in ranked_items if row[1] == required_issuer]
        if issuer_rows:
            selected = next((row for row in issuer_rows if row_has_usable_claim(row, query)), None)
            if selected is None and not usable_ranked_items:
                selected = issuer_rows[0]
            if selected is not None:
                selected_rows.append(selected)
                seen_row_keys.add(row_citation_key(selected))
    fill_rows = usable_ranked_items if usable_ranked_items else fallback_ranked_items
    for row in fill_rows:
        citation_key = row_citation_key(row)
        if citation_key in seen_row_keys:
            continue
        selected_rows.append(row)
        seen_row_keys.add(citation_key)
        if len(selected_rows) >= max_documents:
            break

    evidence_lines: list[str] = []
    source_lines: list[str] = []
    citations: list[dict[str, Any]] = []
    seen_citations: set[str] = set()
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
        if not is_usable_answer_claim(claim, item, query=query):
            claim = f"Ketentuan relevan ditemukan pada dokumen {doc.get('document')}."
        evidence_lines.append(f"- {claim} [{source_index}]")
        source_lines.append(
            f"[{source_index}] {issuer}; {doc.get('source_priority')}; {doc.get('file_role')}; "
            f"{citation_key}."
        )
        citations.append(
            {
                "file_id": item.get("file_id"),
                "block_id": item.get("block_id"),
                "issuer": issuer,
                "document": doc.get("document"),
                "page": citation.get("page"),
                "pasal": citation.get("pasal"),
                "ayat": citation.get("ayat"),
                "huruf": citation.get("huruf"),
                "text": citation.get("text"),
                "quality": quality,
            }
        )
        citation_count += 1
        source_index += 1
        if citation_count >= max_documents:
            break

    related_docs = []
    seen_doc_titles: set[str] = set()
    for doc in documents:
        title = doc.get("document")
        if not title or title in seen_doc_titles:
            continue
        seen_doc_titles.add(title)
        suffix = " (konteks terkait, bukan bukti langsung untuk topik yang diminta)" if doc.get("issuer") in missing_direct_issuers else ""
        related_docs.append(f"- {doc.get('issuer')}: {title}{suffix}")
        if len(related_docs) >= max_documents:
            break

    lines.extend(["Dokumen terkait:", ""])
    lines.extend(related_docs or ["- Tidak ada dokumen terkait yang cukup kuat untuk ditampilkan."])
    lines.append("")
    lines.extend(["Temuan:", ""])
    lines.extend(evidence_lines or ["- Tidak ada butir evidence yang cukup untuk disajikan."])
    lines.extend(["", "Sumber:", ""])
    lines.extend(source_lines or ["- Tidak ada sumber yang digunakan."])

    lines.extend(
        [
            "",
            "Batasan:",
            "- Pasal, ayat, dan huruf hanya dicantumkan jika tersedia pada metadata evidence.",
            "- Jika detail tertentu tidak muncul di sumber yang dikutip, detail tersebut dianggap tidak ditemukan dalam dokumen yang tersedia.",
        ]
    )
    return {
        "query": pack.get("query"),
        "composer": "template",
        "status": status,
        "confidence": confidence,
        "answer": "\n".join(lines).rstrip() + "\n",
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
