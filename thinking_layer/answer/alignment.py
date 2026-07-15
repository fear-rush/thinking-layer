from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re
from typing import Any

from ..retrieval.query_tools import load_stopwords, tokenize_with_stopwords


_GENERIC_QUERY_TERMS = {
    "apa",
    "saja",
    "aturan",
    "peraturan",
    "ketentuan",
    "terkait",
    "tentang",
    "menurut",
    "berdasarkan",
    "nomor",
    "tahun",
    "pasal",
    "ayat",
    "huruf",
    "ojk",
    "bi",
    "pojk",
    "pbi",
    "padg",
    "seojk",
    "bank",
    "indonesia",
    "perusahaan",
    "wajib",
    "kewajiban",
    "diwajibkan",
    "harus",
    "dipatuhi",
    "dipenuhi",
    "memenuhi",
    "penuhi",
    "sanksi",
    "denda",
    "tugas",
    "fungsi",
    "wewenang",
    "definisi",
    "pengertian",
    "berapa",
    "batas",
    "minimum",
    "maksimum",
    "jumlah",
    "terbaru",
    "berlaku",
    "status",
    "current",
    "latest",
    "bandingkan",
    "komparasi",
    "lembaga",
    "keuangan",
}

_TOKEN_ALIASES = {
    "periklanan": "iklan",
    "mengiklankan": "iklan",
    "diiklankan": "iklan",
    "promosi": "promosi",
    "promo": "promosi",
    "pembawaan": "bawa",
    "membawa": "bawa",
    "dibawa": "bawa",
    "pelaporan": "lapor",
    "melaporkan": "lapor",
    "laporan": "lapor",
    "perizinan": "izin",
    "persetujuan": "izin",
    "pengaduan": "adu",
    "perlindungan": "lindung",
    "pemberian": "beri",
    "memberikan": "beri",
    "membagikan": "beri",
    "dibagikan": "beri",
    "pelanggan": "konsumen",
    "menyelesaikan": "selesai",
    "penyelesaian": "selesai",
    "perpanjangan": "perpanjang",
    "memperpanjang": "perpanjang",
    "mengirim": "sampai",
    "mengirimkan": "sampai",
    "menyampaikan": "sampai",
    "penyampaian": "sampai",
    "dipenuhi": "penuhi",
    "memenuhi": "penuhi",
}

_PREDICATE_PATTERNS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "obligation": (
        ("kewajiban", "wajib", "harus", "diwajibkan", "dipatuhi"),
        (
            "wajib",
            "harus",
            "dilarang",
            "berkewajiban",
            "pihak yang wajib",
            "dengan memperhatikan ketentuan",
        ),
    ),
    "sanction": (
        ("sanksi", "denda", "terlambat", "pelanggaran"),
        ("sanksi", "denda", "teguran", "pembatasan", "pencabutan", "dikenai", "dijatuhi"),
    ),
    "definition": (
        ("definisi", "pengertian", "apa itu", "yang dimaksud"),
        ("adalah", "yang dimaksud", "didefinisikan", "selanjutnya disingkat"),
    ),
    "duties": (
        ("tugas", "fungsi", "wewenang", "tanggung jawab"),
        ("tugas", "fungsi", "wewenang", "tanggung jawab", "bertanggung jawab"),
    ),
    "prohibition": (
        ("larangan", "dilarang", "tidak boleh", "bolehkah"),
        ("dilarang", "tidak boleh", "larangan"),
    ),
    "permission": (
        ("boleh", "dapatkah", "diizinkan"),
        (
            "dapat menempatkan",
            "boleh menempatkan",
            "diizinkan menempatkan",
            "sepanjang memperoleh izin",
            "tidak berlaku jika",
            "diperbolehkan",
        ),
    ),
}


@dataclass(frozen=True)
class AnswerAlignment:
    accepted: bool
    distinctive_terms: tuple[str, ...]
    matched_distinctive_terms: tuple[str, ...]
    distinctive_ratio: float
    predicate: str | None
    predicate_matched: bool
    legal_anchor: str | None
    legal_anchor_matched: bool
    value_required: bool
    value_matched: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_token(token: str) -> str:
    return _TOKEN_ALIASES.get(token.casefold(), token.casefold())


def _text_for_item(item: dict[str, Any]) -> tuple[str, str]:
    citation = item.get("citation") or {}
    document = str(citation.get("document") or item.get("document_title") or "")
    claim = str(item.get("assembled_text") or item.get("text") or item.get("snippet") or "")
    return document, claim


def _predicates_for(query: str) -> tuple[str, ...]:
    query_l = query.casefold()
    return tuple(
        name
        for name, (query_terms, _) in _PREDICATE_PATTERNS.items()
        if any(term in query_l for term in query_terms)
    )


def _predicate_matches(predicate: str | None, claim: str) -> bool:
    if predicate is None:
        return True
    claim_l = claim.casefold()
    return any(term in claim_l for term in _PREDICATE_PATTERNS[predicate][1])


def _value_required(query: str) -> bool:
    query_l = query.casefold()
    if any(term in query_l for term in ("berapa", "batas", "jumlah", "paling sedikit", "paling banyak")):
        return True
    # ``minimum`` can describe the requested scope (for example, "tugas
    # minimum") rather than a numeric value.  Only bind it to the value gate
    # when the query names a measurable quantity.
    return bool(
        re.search(
            r"\b(?:nilai|modal|persentase|rasio|jangka\s+waktu|saldo|tarif|biaya)\s+(?:minimum|maksimum)\b|"
            r"\b(?:minimum|maksimum)\s+(?:nilai|modal|persentase|rasio|jangka\s+waktu|saldo|tarif|biaya)\b",
            query_l,
        )
    )


def _legal_anchor_match(query: str, claim: str) -> tuple[str | None, bool]:
    query_l = query.casefold()
    claim_l = claim.casefold()
    requested = [
        anchor
        for anchor in ("izin", "persetujuan")
        if re.search(rf"(?<!\w){anchor}(?!\w)", query_l)
    ]
    if not requested:
        return None, True
    matched = [
        anchor
        for anchor in requested
        if re.search(rf"(?<!\w){anchor}(?!\w)", claim_l)
    ]
    return "|".join(requested), bool(matched)


def _value_matches(claim: str) -> bool:
    claim_l = claim.casefold()
    has_number = bool(re.search(r"(?<![a-z])\d+(?:[.,]\d+)*(?![a-z])", claim_l))
    has_value_context = bool(
        re.search(
            r"\b(?:rp|usd|persen|hari|bulan|tahun|jam|menit|sebesar|setara|paling\s+sedikit|paling\s+banyak)\b|%",
            claim_l,
        )
    )
    return has_number and has_value_context


def answer_alignment(
    query: str,
    item: dict[str, Any],
    *,
    plan: dict[str, Any] | None = None,
    minimum_distinctive_ratio: float = 0.75,
    allow_missing_value: bool = False,
    allow_missing_predicate: bool = False,
) -> AnswerAlignment:
    document, claim = _text_for_item(item)
    stopwords = load_stopwords()
    raw_terms = tokenize_with_stopwords(query, stopwords)
    lexical_distinctive_terms = [
        _normalize_token(term)
        for term in raw_terms
        if term.casefold() not in _GENERIC_QUERY_TERMS and not re.fullmatch(r"\d+(?:[/.]\d+)*", term)
    ]
    consumed_terms: set[str] = set()
    matched_concepts: list[str] = []
    evidence_concepts: set[str] = set()
    query_l = query.casefold()
    evidence_l = f"{document} {claim}".casefold()
    for concept in (plan or {}).get("entity_concepts") or []:
        query_patterns = [str(value).casefold() for value in concept.get("query_patterns") or []]
        if not any(re.search(rf"(?<!\w){re.escape(pattern)}(?!\w)", query_l) for pattern in query_patterns):
            continue
        concept_term = f"entity:{concept.get('name')}"
        matched_concepts.append(concept_term)
        for pattern in query_patterns:
            consumed_terms.update(_normalize_token(term) for term in tokenize_with_stopwords(pattern, stopwords))
        evidence_patterns = [str(value).casefold() for value in concept.get("evidence_patterns") or []]
        if any(re.search(rf"(?<!\w){re.escape(pattern)}(?!\w)", evidence_l) for pattern in evidence_patterns):
            evidence_concepts.add(concept_term)

    distinctive_terms = tuple(
        dict.fromkeys(
            [
                *(term for term in lexical_distinctive_terms if term not in consumed_terms),
                *matched_concepts,
            ]
        )
    )
    evidence_terms = {
        _normalize_token(term)
        for term in tokenize_with_stopwords(f"{document} {claim}", stopwords)
    }
    evidence_terms.update(evidence_concepts)
    matched_terms = tuple(term for term in distinctive_terms if term in evidence_terms)
    ratio = len(matched_terms) / max(1, len(distinctive_terms)) if distinctive_terms else 1.0
    required_hits = math.ceil(len(distinctive_terms) * minimum_distinctive_ratio) if distinctive_terms else 0
    distinctive_ok = not distinctive_terms or len(matched_terms) >= max(1, required_hits)

    predicates = _predicates_for(query)
    predicate = "|".join(predicates) or None
    predicate_matched = not predicates or any(_predicate_matches(value, claim) for value in predicates)
    legal_anchor, legal_anchor_matched = _legal_anchor_match(query, claim)
    value_required = _value_required(query)
    value_matched = _value_matches(claim) if value_required else True

    reasons: list[str] = []
    if not distinctive_ok:
        reasons.append("insufficient_distinctive_query_alignment")
    if not predicate_matched:
        reasons.append(
            f"predicate_deferred_for_compound_query:{predicate}"
            if allow_missing_predicate
            else f"predicate_not_supported:{predicate}"
        )
    if not legal_anchor_matched:
        reasons.append(f"legal_anchor_not_supported:{legal_anchor}")
    if not value_matched and not allow_missing_value:
        reasons.append("requested_value_not_supported")
    if not value_matched and allow_missing_value:
        reasons.append("requested_value_deferred_for_ambiguity")
    deferred_support_ok = True
    if allow_missing_predicate and allow_missing_value and predicates and value_required:
        deferred_support_ok = predicate_matched or value_matched
    return AnswerAlignment(
        accepted=(
            distinctive_ok
            and (predicate_matched or allow_missing_predicate)
            and legal_anchor_matched
            and (value_matched or allow_missing_value)
            and deferred_support_ok
        ),
        distinctive_terms=distinctive_terms,
        matched_distinctive_terms=matched_terms,
        distinctive_ratio=round(ratio, 3),
        predicate=predicate,
        predicate_matched=predicate_matched,
        legal_anchor=legal_anchor,
        legal_anchor_matched=legal_anchor_matched,
        value_required=value_required,
        value_matched=value_matched,
        reasons=tuple(reasons),
    )


def has_lifecycle_provenance(item: dict[str, Any]) -> bool:
    return (
        isinstance(item.get("is_current"), bool)
        or bool(item.get("lifecycle_status"))
        or bool(item.get("repeal_date"))
        or bool(item.get("supersedes"))
        or bool(item.get("amends"))
    )


def is_lifecycle_query(query: str, plan: dict[str, Any] | None = None) -> bool:
    """Return whether the user asks for a document's current legal status.

    The query lexicon's ``latest`` intent also covers substantive amendment
    questions.  Those must remain answerable from amendment clauses, so this
    boundary deliberately requires explicit status language.
    """

    query_l = normalize_space_for_match(query)
    lifecycle_patterns = (
        "masih berlaku",
        "status berlaku",
        "status keberlakuan",
        "berlaku saat ini",
        "yang berlaku saat ini",
        "peraturan terbaru",
        "regulasi terbaru",
        "sudah dicabut",
        "telah dicabut",
        "current regulation",
        "latest regulation",
    )
    if any(pattern in query_l for pattern in lifecycle_patterns):
        return True
    intents = set((plan or {}).get("intents") or [])
    return "latest" in intents and query_l.strip() in {"terbaru", "latest", "current"}


def normalize_space_for_match(text: str) -> str:
    return " ".join(text.casefold().split())
