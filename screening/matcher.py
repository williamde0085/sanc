from rapidfuzz import fuzz

from screening.models import Candidate, Query, ScoredCandidate
from screening.normalize import normalize_identifier, normalize_name, parse_year_or_date

# бампать при любом изменении логики скоринга/классификации - пишется в аудит
MATCHER_VERSION = "v1"


def name_similarity(query_name, candidate):
    q = normalize_name(query_name)
    names = [candidate.primary_name] + [a.get("name", "") for a in candidate.aliases]
    best_score, best_name = 0.0, candidate.primary_name
    for name in names:
        c = normalize_name(name or "")
        if not c:
            continue
        # WRatio ловит опечатки, token_set_ratio - перестановку слов
        s = 0.55 * fuzz.WRatio(q, c) + 0.45 * fuzz.token_set_ratio(q, c)
        if s > best_score:
            best_score, best_name = s, name
    return round(best_score, 2), best_name

def _id_match(query, candidate):
    want =normalize_identifier(query.identifier)
    if not want:
        return False
    return any(normalize_identifier(str(i.get("number") or "")) == want for i in candidate.identifiers)


def _country_match(query, candidate):
    if not query.country:
        return False
    want =normalize_name(query.country)
    return any(normalize_name(c) == want for c in candidate.countries if c)


def _dob_match(query_dob, candidate_dobs):
    if not query_dob:
        return False
    q = parse_year_or_date(query_dob)
    if q is None:
        return False
    for raw in candidate_dobs:
        c =parse_year_or_date(raw)
        if c is None or c[0] != q[0]:
            continue
        # год совпал; месяц и день сверяем, только если есть с обеих сторон
        if (q[1] is None or c[1] is None or q[1] == c[1]) and (q[2] is None or c[2] is None or q[2] == c[2]):
            return True
    return False

def score_candidate(query: Query, candidate: Candidate) -> ScoredCandidate:
    name_score, matched_name = name_similarity(query.name, candidate)
    id_ok = _id_match(query, candidate)
    country_ok = _country_match(query, candidate)
    dob_ok = _dob_match(query.date_of_birth, candidate.dates_of_birth)
    type_ok = bool(
        query.entity_type
        and candidate.entity_type
        and normalize_name(query.entity_type) == normalize_name(candidate.entity_type)
    )
    score = name_score
    reasons = ["NAME_SIMILARITY"]
    if id_ok:
        score = max(score, 99.5)
        reasons.append("EXACT_IDENTIFIER")
    if country_ok:
        score = min(100.0, score + 2)
        reasons.append("COUNTRY_MATCH")
    if dob_ok:
        score = min(100.0, score + 2)
        reasons.append("DOB_MATCH")
    if type_ok:
        score = min(100.0, score + 1)
        reasons.append("ENTITY_TYPE_MATCH")
    if matched_name != candidate.primary_name:
        reasons.append("ALIAS_MATCH")

    return ScoredCandidate(
        candidate=candidate,
        score=round(score, 2),
        name_score=name_score,
        matched_name=matched_name,
        identifier_match=id_ok,
        country_match=country_ok,
        dob_match=dob_ok,
        entity_type_match=type_ok,
        reason_codes=tuple(reasons),
    )

def classify(scored, review_threshold, match_threshold, require_secondary):
    if not scored or scored[0].score < review_threshold:
        return "NO_MATCH", ("BELOW_REVIEW_THRESHOLD",)
    top =scored[0]
    second = scored[1].score if len(scored) > 1 else 0.0
    ambiguous = top.score - second < 3.0
    has_secondary = top.identifier_match or top.country_match or top.dob_match or top.entity_type_match

    if top.score >= match_threshold and not ambiguous:
        if require_secondary and not has_secondary:
            return "POSSIBLE_MATCH", ("SECONDARY_IDENTIFIER_REQUIRED",)
        return "MATCH", ("ABOVE_MATCH_THRESHOLD",)

    reasons = ["REVIEW_REQUIRED"]
    if ambiguous:
        reasons.append("AMBIGUOUS_TOP_CANDIDATES")
    return "POSSIBLE_MATCH", tuple(reasons)
