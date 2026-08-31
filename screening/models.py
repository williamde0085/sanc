from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Query:
    name: str
    country: str | None = None
    date_of_birth: str | None = None
    identifier: str | None = None
    entity_type: str | None = None


@dataclass(frozen=True)
class Candidate:
    entity_id: str
    primary_name: str
    normalized_name: str
    source_list: str
    entity_type: str | None
    programs: list[str]
    countries: list[str]
    dates_of_birth: list[str]
    identifiers: list[dict[str, Any]]
    aliases: list[dict[str, Any]]
    source_version: str


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: Candidate
    score: float
    name_score: float
    matched_name: str
    identifier_match: bool = False
    country_match: bool = False
    dob_match: bool = False
    entity_type_match: bool = False
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
