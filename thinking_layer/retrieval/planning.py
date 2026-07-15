from __future__ import annotations

import argparse
import re
from typing import Any

from ..config.heuristics import heuristic_section
from ..common.text import normalize_space
from .query_tools import contains_pattern, load_query_lexicon, load_stopwords, matched_items, query_overlap_score, tokenize_with_stopwords, unique_keep_order


_LEGAL_ARTICLE_RE = re.compile(r"\bPasal\s+(\d+[A-Z]?)\b", re.IGNORECASE)
_LEGAL_AYAT_RE = re.compile(r"\bAyat\s*\(?\s*(\d+[a-z]?)\s*\)?", re.IGNORECASE)
_LEGAL_INLINE_AYAT_RE = re.compile(r"\bPasal\s+\d+[A-Z]?\s*\(\s*(\d+[a-z]?)\s*\)", re.IGNORECASE)
_LEGAL_HURUF_RE = re.compile(r"\bHuruf\s+([a-z])\b", re.IGNORECASE)
_REGULATION_TYPE_RE = re.compile(r"\b(PBI|POJK|PADG|SEOJK)\b", re.IGNORECASE)
_FOUR_DIGIT_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def parse_legal_query_constraints(query: str) -> dict[str, str]:
    """Extract explicit legal anchors without inferring unstated provisions.

    These values are query constraints, not search synonyms.  A requested
    ``Pasal 5`` may only be satisfied by a row whose v2 legal path contains
    that exact Pasal.  Regulation metadata is intentionally conservative:
    only an explicitly written type/number/year is captured.
    """

    constraints: dict[str, str] = {}
    if match := _LEGAL_ARTICLE_RE.search(query):
        constraints["pasal"] = f"Pasal {match.group(1).upper()}"
    ayat_match = _LEGAL_AYAT_RE.search(query) or _LEGAL_INLINE_AYAT_RE.search(query)
    if ayat_match:
        constraints["ayat"] = f"({ayat_match.group(1).lower()})"
    if match := _LEGAL_HURUF_RE.search(query):
        constraints["huruf"] = f"huruf {match.group(1).lower()}"

    if match := _REGULATION_TYPE_RE.search(query):
        regulation_type = match.group(1).upper()
        constraints["regulation_type"] = regulation_type
        tail = query[match.end() : match.end() + 80]
        number_match = re.match(r"\s*(?:Nomor|No\.?)\s*(\d+)", tail, flags=re.IGNORECASE)
        if number_match is None:
            number_match = re.match(r"\s*(\d+)(?=\s*(?:/|Tahun\b))", tail, flags=re.IGNORECASE)
        if number_match:
            constraints["regulation_number"] = number_match.group(1)
        years = _FOUR_DIGIT_YEAR_RE.findall(tail)
        if years:
            constraints["year"] = years[-1]
    return constraints

def ordered_expansions(query: str, item: dict[str, Any]) -> list[str]:
    expansions = item.get("expansions") or []
    query_terms = set(tokenize_with_stopwords(query, load_stopwords()))

    def priority(value: str) -> int:
        value_terms = set(tokenize_with_stopwords(value, load_stopwords()))
        return len(query_terms & value_terms)

    return sorted(expansions, key=priority, reverse=True)

def ordered_matches(query: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def priority(item: dict[str, Any]) -> tuple[float, int]:
        matched = " ".join(item.get("matched_patterns") or [])
        expansions = " ".join(item.get("expansions") or [])
        return (
            query_overlap_score(query, matched) + query_overlap_score(query, expansions) * 0.15,
            max((len(pattern) for pattern in item.get("matched_patterns") or []), default=0),
        )

    return sorted(items, key=priority, reverse=True)

def should_expand_entity(entity: dict[str, Any], has_topic_matches: bool) -> bool:
    config = heuristic_section("retrieval_ranking", "query_planning")
    name = entity.get("name")
    if has_topic_matches and name in set(config.get("generic_bank_entity_names") or []):
        return False
    if name == config.get("bank_entity_name", "bank"):
        matched = {pattern.lower() for pattern in entity.get("matched_patterns") or []}
        return bool(matched - set(config.get("bank_entity_generic_patterns") or ["bank"]))
    return True

def infer_issuers(query: str, topic_matches: list[dict[str, Any]], issuer_matches: list[dict[str, Any]]) -> list[str | None]:
    config = heuristic_section("retrieval_ranking", "query_planning")
    issuers = [item["issuer"] for item in issuer_matches if item.get("issuer")]
    issuers.extend(item["issuer"] for item in topic_matches if item.get("issuer"))
    issuer_patterns = config.get("issuer_patterns") or {}
    if any(contains_pattern(query, pattern) for pattern in issuer_patterns.get("OJK", ["ojk"])) and "BI" not in issuers:
        issuers.append("OJK")
    if any(contains_pattern(query, pattern) for pattern in issuer_patterns.get("BI", ["bi", "bank indonesia"])) and "BI" not in issuers:
        issuers.append("BI")
    if contains_pattern(query, "bank") and not issuers:
        issuers.append(str(config.get("bank_default_issuer", "OJK")))
    if not issuers:
        issuers.append(None)
    return unique_keep_order(issuers)


def direct_enumeration_nouns(query: str, config: dict[str, Any]) -> list[str]:
    """Return queried legal nouns only for an explicit enumeration-style question."""
    question_patterns = config.get("question_patterns") or []
    if not any(contains_pattern(query, pattern) for pattern in question_patterns):
        return []
    return [noun for noun in config.get("legal_nouns") or [] if contains_pattern(query, noun)]


def enumeration_subject_terms(query: str, entity: dict[str, Any], max_terms: int) -> list[str]:
    """Use existing entity aliases, preferring the stated term and one short alias.

    A single-token entity pattern is treated as an acronym/abbreviation candidate.
    This keeps the expansion lexicon-driven rather than coupling it to a specific
    regulated subject such as PJP.
    """
    matched = sorted(
        entity.get("matched_patterns") or [],
        key=lambda pattern: len(normalize_space(pattern).split()),
        reverse=True,
    )
    patterns = entity.get("patterns") or []
    abbreviations = [pattern for pattern in patterns if len(normalize_space(pattern).split()) == 1]
    expansions = ordered_expansions(query, entity)
    # The most specific stated term is enough; shorter matched aliases can be
    # generic fragments (for example, "jasa pembayaran").
    candidates = unique_keep_order([*matched[:1], *abbreviations, *expansions])
    return [normalize_space(term) for term in candidates if normalize_space(term)][:max_terms]


def direct_enumeration_searches(
    query: str,
    entities: list[dict[str, Any]],
    issuers: list[str | None],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create bounded subject+noun+marker searches for legal lists.

    These queries are intentionally only emitted when the user asks an explicit
    Indonesian enumeration question and names both a recognized legal subject and
    a configured legal noun.  They target v2 leaves whose retrieval context
    includes the governing lead-in (for example, ``... aktivitas yang meliputi``).
    """
    nouns = direct_enumeration_nouns(query, config)
    markers = config.get("enumeration_markers") or []
    if not nouns or not markers:
        return []

    searches: list[dict[str, Any]] = []
    max_subject_terms = int(config.get("max_subject_terms", 2))
    target_issuer = issuers[0] if issuers else None
    for entity in entities:
        for subject in enumeration_subject_terms(query, entity, max_subject_terms):
            for noun in nouns:
                for marker in markers:
                    searches.append(
                        {
                            "query": normalize_space(f"{subject} {noun} {marker}"),
                            "issuer": target_issuer,
                            "role": "primary_regulation",
                            "include_secondary": True,
                            "reason": f"direct_enumeration:{noun}:{marker}",
                        }
                    )
    return unique_keep_order(searches)[: int(config.get("max_searches", 2))]


def predicate_searches(query: str, issuer: str | None, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Add one bounded lexical variant for a stated legal predicate.

    Indonesian legal questions commonly use the noun ``larangan`` while the
    operative clause uses ``dilarang``.  This is a search representation only;
    answer alignment still requires the operative predicate in the evidence.
    """

    query_l = query.casefold()
    for source, target in (config.get("predicate_replacements") or {}).items():
        if not contains_pattern(query_l, str(source)):
            continue
        expanded = re.sub(
            rf"(?<!\w){re.escape(str(source))}(?!\w)",
            str(target),
            query,
            count=1,
            flags=re.IGNORECASE,
        )
        if str(source).casefold() == "boleh" and str(target).casefold() == "dapat":
            expanded = re.sub(r"(?<!\w)(?:wajib|harus)(?!\w)", " ", expanded, flags=re.IGNORECASE)
        lexical_aliases = {
            "membagikan": "memberikan",
            "dibagikan": "diberikan",
            "pelanggan": "konsumen",
            "perusahaan lain": "pihak lain",
        }
        for plain_term, legal_term in lexical_aliases.items():
            expanded = re.sub(
                rf"(?<!\w){re.escape(plain_term)}(?!\w)",
                legal_term,
                expanded,
                flags=re.IGNORECASE,
            )
        if normalize_space(expanded).casefold() == normalize_space(query).casefold():
            continue
        return [
            {
                "query": normalize_space(expanded),
                "issuer": issuer,
                "role": "primary_regulation",
                "include_secondary": True,
                "reason": f"predicate:{source}:{target}",
            }
        ]
    return []


def legal_alias_searches(query: str, issuers: list[str | None]) -> list[dict[str, Any]]:
    """Translate common-language legal verbs without changing answer meaning."""

    expanded = query
    aliases = {
        "pemberian": "memberikan",
        "membagikan": "memberikan",
        "dibagikan": "diberikan",
        "pelanggan": "konsumen",
        "perusahaan lain": "pihak lain",
        "memberi tahu": "memberitahukan",
        "diberi tahu": "diberitahukan",
        "perpanjangan": "memperpanjang",
    }
    for plain_term, legal_term in aliases.items():
        expanded = re.sub(
            rf"(?<!\w){re.escape(plain_term)}(?!\w)",
            legal_term,
            expanded,
            flags=re.IGNORECASE,
        )
    expanded = normalize_space(expanded)
    if expanded.casefold() == normalize_space(query).casefold():
        return []
    expanded_l = expanded.casefold()
    if "memberikan" in expanded_l and "data" in expanded_l and "konsumen" in expanded_l and "pihak lain" in expanded_l:
        expanded = "memberikan data konsumen kepada pihak lain"
    return [
        {
            "query": expanded,
            "issuer": issuer,
            "role": "primary_regulation",
            "include_secondary": True,
            "reason": "legal_alias",
        }
        for issuer in issuers or [None]
    ]


def unsupported_source_for(query: str) -> str | None:
    query_l = query.casefold()
    if "bappebti" in query_l and ("menurut" in query_l or "bukan ojk" in query_l):
        return "BAPPEBTI"
    return None


def ambiguity_for(
    query: str,
    entity_matches: list[dict[str, Any]],
    topic_matches: list[dict[str, Any]],
    explicit_issuers: list[str],
) -> str | None:
    if explicit_issuers:
        return None
    query_l = query.casefold()
    topic_names = {str(item.get("name")) for item in topic_matches}
    entity_names = {str(item.get("name")) for item in entity_matches}
    if "lembaga keuangan" in query_l and any(term in query_l for term in ("data", "pelanggan", "konsumen")):
        return "institution_type"
    bank_subtypes = (
        "bank umum",
        "bpr",
        "bprs",
        "bank perekonomian rakyat",
        "bank perkreditan rakyat",
        "bank syariah",
        "bank umum syariah",
    )
    if "bank" in entity_names and "capital" in topic_names and not any(term in query_l for term in bank_subtypes):
        return "bank_type"
    return None


def build_query_plan(query: str, max_searches: int = 12) -> dict[str, Any]:
    planning_config = heuristic_section("retrieval_ranking", "query_planning")
    legal_constraints = parse_legal_query_constraints(query)
    lexicon = load_query_lexicon()
    intent_matches = matched_items(query, lexicon.get("intents", []))
    issuer_matches = matched_items(query, lexicon.get("issuers", []))
    entity_matches = ordered_matches(query, matched_items(query, lexicon.get("entities", [])))
    topic_matches = ordered_matches(query, matched_items(query, lexicon.get("topics", [])))

    intents = [item["intent"] for item in intent_matches] or [str(planning_config.get("default_intent", "find_regulations"))]
    issuers = infer_issuers(query, topic_matches, issuer_matches)
    explicit_issuers = unique_keep_order([item["issuer"] for item in issuer_matches if item.get("issuer")])
    legal_issuer = {
        "PBI": "BI",
        "PADG": "BI",
        "POJK": "OJK",
        "SEOJK": "OJK",
    }.get(legal_constraints.get("regulation_type", ""))
    if legal_issuer and not explicit_issuers:
        explicit_issuers = [legal_issuer]
    if explicit_issuers:
        issuers = explicit_issuers
    else:
        entity_issuers = unique_keep_order([item["issuer"] for item in entity_matches if item.get("issuer")])
        if entity_issuers:
            issuers = entity_issuers
    ambiguity = ambiguity_for(query, entity_matches, topic_matches, explicit_issuers)
    if ambiguity == "institution_type":
        issuers = ["BI", "OJK"]
    unsupported_source = unsupported_source_for(query)
    if unsupported_source:
        return {
            "raw_query": query,
            "intents": intents,
            "issuers": [],
            "entities": [item["name"] for item in entity_matches],
            "topics": [item["name"] for item in topic_matches],
            "legal_constraints": legal_constraints,
            "ambiguity": None,
            "unsupported_source": unsupported_source,
            "searches": [],
        }
    entity_terms: list[str] = []
    topic_terms: list[str] = []
    for item in entity_matches:
        if not should_expand_entity(item, bool(topic_matches)):
            continue
        entity_terms.extend(item.get("expansions") or [])
    for item in topic_matches:
        topic_terms.extend(item.get("expansions") or [])

    base_terms = unique_keep_order([query, *topic_terms, *entity_terms])
    searches: list[dict[str, Any]] = []
    generic_bank_names = set(planning_config.get("generic_bank_entity_names") or ["bank"])

    # Raw query remains useful, but it should not be the only search.
    searches.append(
        {
            "query": query,
            "issuer": explicit_issuers[0] if len(explicit_issuers) == 1 else (None if len([i for i in issuers if i]) > 1 else issuers[0]),
            "role": None,
            "include_secondary": True,
            "reason": "raw_user_query",
        }
    )

    predicate_issuers = (
        explicit_issuers
        if explicit_issuers
        else (issuers if ambiguity == "institution_type" else issuers[:1])
    )
    for predicate_issuer in predicate_issuers or [None]:
        searches.extend(predicate_searches(query, predicate_issuer, planning_config))

    alias_issuers = explicit_issuers or issuers
    searches.extend(legal_alias_searches(query, alias_issuers))

    searches.extend(
        direct_enumeration_searches(
            query,
            [item for item in entity_matches if item.get("name") not in generic_bank_names],
            issuers,
            planning_config.get("direct_enumeration") or {},
        )
    )

    for entity in [item for item in entity_matches if item.get("name") not in generic_bank_names]:
        if not should_expand_entity(entity, bool(topic_matches)):
            continue
        for expansion in ordered_expansions(query, entity):
            for issuer in issuers:
                searches.append(
                    {
                        "query": expansion,
                        "issuer": issuer,
                        "role": "primary_regulation",
                        "include_secondary": True,
                        "reason": f"entity:{entity['name']}",
                    }
                )

    topic_search_groups: list[list[dict[str, Any]]] = []
    for topic in topic_matches:
        topic_searches: list[dict[str, Any]] = []
        topic_issuer = topic.get("issuer")
        if explicit_issuers:
            topic_issuers = explicit_issuers
        elif topic_issuer:
            topic_issuers = [topic_issuer]
        else:
            topic_issuers = issuers
        for expansion in ordered_expansions(query, topic):
            for issuer in topic_issuers:
                topic_searches.append(
                    {
                        "query": normalize_space(expansion),
                        "issuer": issuer,
                        "role": "primary_regulation",
                        "include_secondary": True,
                        "reason": f"topic:{topic['name']}",
                    }
                )
        topic_search_groups.append(topic_searches)

    # Interleave relevant topics so one broad topic cannot consume the bounded
    # search plan before a more specific sibling gets a search slot.
    for expansion_index in range(max((len(group) for group in topic_search_groups), default=0)):
        for group in topic_search_groups:
            if expansion_index < len(group):
                searches.append(group[expansion_index])

    if not topic_matches and not [item for item in entity_matches if item.get("name") not in generic_bank_names]:
        for entity in entity_matches:
            if not should_expand_entity(entity, bool(topic_matches)):
                continue
            for expansion in entity.get("expansions") or []:
                for issuer in issuers:
                    searches.append(
                        {
                            "query": expansion,
                            "issuer": issuer,
                            "role": "primary_regulation",
                            "include_secondary": True,
                            "reason": f"entity:{entity['name']}",
                        }
                    )

    # Intent-specific broadening.
    intent_expansions = planning_config.get("intent_expansions") or {}
    for intent in intents:
        expansion_config = intent_expansions.get(intent)
        if not expansion_config:
            continue
        for term in expansion_config.get("queries") or []:
            searches.append(
                {
                    "query": term,
                    "issuer": issuers[0],
                    "role": expansion_config.get("role"),
                    "include_secondary": bool(expansion_config.get("include_secondary", True)),
                    "reason": f"intent:{intent}",
                }
            )

    if len(searches) == 1:
        for term in base_terms[1:]:
            searches.append({"query": term, "issuer": issuers[0], "role": None, "include_secondary": True, "reason": "lexical_expansion"})

    searches = unique_keep_order(searches)
    return {
        "raw_query": query,
        "intents": intents,
        "issuers": issuers,
        "entities": [item["name"] for item in entity_matches],
        "topics": [item["name"] for item in topic_matches],
        "legal_constraints": legal_constraints,
        "ambiguity": ambiguity,
        "unsupported_source": None,
        "searches": searches[:max_searches],
    }

def format_query_plan(plan: dict[str, Any]) -> str:
    lines = [
        "# Query Plan",
        "",
        f"- Raw query: `{plan['raw_query']}`",
        f"- Intents: `{plan['intents']}`",
        f"- Issuers: `{plan['issuers']}`",
        f"- Entities: `{plan['entities']}`",
        f"- Topics: `{plan['topics']}`",
        "",
        "## Searches",
        "",
    ]
    for index, search in enumerate(plan["searches"], start=1):
        lines.append(
            f"{index}. `{search['query']}` | issuer `{search.get('issuer')}` | role `{search.get('role')}` | reason `{search['reason']}`"
        )
    return "\n".join(lines) + "\n"

def cmd_plan_query(args: argparse.Namespace) -> None:
    plan = build_query_plan(args.query, max_searches=args.max_searches)
    print(format_query_plan(plan))
