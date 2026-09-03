from typing import Literal

from pydantic import BaseModel, Field, field_validator

Outcome = Literal["MATCH", "POSSIBLE_MATCH", "NO_MATCH"]


class ScreenRequest(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    country: str | None = Field(default=None, max_length=120)
    date_of_birth: str | None = Field(default=None, max_length=32)
    identifier: str | None = Field(default=None, max_length=120)
    entity_type: str | None = Field(default=None, max_length=80)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name is too short")
        return v


class CandidateOut(BaseModel):
    entity_id: str
    primary_name: str
    matched_name: str
    source_list: str
    entity_type: str | None
    score: float
    name_score: float
    reason_codes: list[str]


class ScreenResponse(BaseModel):
    decision_id: str
    request_id: str
    outcome: Outcome
    list_version: str
    matcher_version: str
    reason_codes: list[str]
    candidates: list[CandidateOut]
    human_review_required: bool


class ReviewRequest(BaseModel):
    outcome: Literal["CONFIRMED_MATCH", "FALSE_POSITIVE", "INSUFFICIENT_INFORMATION"]
    notes: str | None = Field(default=None, max_length=2000)
