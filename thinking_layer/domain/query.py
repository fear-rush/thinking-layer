from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class AnswerMode(StrEnum):
    DOCUMENT_DISCOVERY = "document_discovery"
    EXACT_LOOKUP = "exact_lookup"
    RULE = "rule"
    DEFINITION = "definition"
    VALUE = "value"
    PROCEDURE = "procedure"
    COMPARISON = "comparison"
    LIFECYCLE = "lifecycle"


class RequestedShape(StrEnum):
    DOCUMENTS = "documents"
    FINDINGS = "findings"
    COMPARISON = "comparison"


@dataclass(frozen=True)
class ExplicitConstraints:
    issuer: str | None = None
    instrument_type: str | None = None
    instrument_number: str | None = None
    instrument_year: int | None = None
    pasal: str | None = None
    ayat: str | None = None
    huruf: str | None = None
    as_of: date | None = None

    def __post_init__(self) -> None:
        if self.instrument_year is not None and not 1900 <= self.instrument_year <= 3000:
            raise ValueError("instrument_year must be a four-digit year")


@dataclass(frozen=True)
class QuerySpec:
    raw_query: str
    mode: AnswerMode
    requested_predicate: str
    requested_shape: RequestedShape
    constraints: ExplicitConstraints = field(default_factory=ExplicitConstraints)
    ambiguity_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        raw_query = " ".join(self.raw_query.split())
        predicate = " ".join(self.requested_predicate.split())
        if not raw_query:
            raise ValueError("raw_query is required")
        if not predicate:
            raise ValueError("requested_predicate is required")
        object.__setattr__(self, "raw_query", raw_query)
        object.__setattr__(self, "requested_predicate", predicate)
        object.__setattr__(self, "ambiguity_reasons", tuple(self.ambiguity_reasons))
