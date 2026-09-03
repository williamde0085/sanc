from screening.matcher import classify, name_similarity, score_candidate
from screening.models import Candidate, Query, ScoredCandidate


def _candidate(**kw):
    base = dict(
        entity_id="SDN:1",
        primary_name="Ivan Petrov",
        normalized_name="IVAN PETROV",
        source_list="SDN",
        entity_type="Individual",
        programs=[],
        countries=["Kazakhstan"],
        dates_of_birth=["1975"],
        identifiers=[{"type": "Passport", "number": "KZ123456"}],
        aliases=[{"name": "Ivan Petroff", "type": "a.k.a."}],
        source_version="test",
    )
    base.update(kw)
    return Candidate(**base)


def _scored(score, **kw):
    base = dict(
        candidate=_candidate(),
        score=score,
        name_score=score,
        matched_name="Ivan Petrov",
        identifier_match=False,
        country_match=False,
        dob_match=False,
        entity_type_match=False,
        reason_codes=("NAME_SIMILARITY",),
    )
    base.update(kw)
    return ScoredCandidate(**base)


def test_name_similarity_exact():
    score, name = name_similarity("Ivan Petrov", _candidate())
    assert score == 100.0
    assert name == "Ivan Petrov"


def test_name_similarity_tolerates_word_order():
    score, _ = name_similarity("Petrov Ivan", _candidate(aliases=[]))
    assert score >= 90


def test_name_similarity_picks_best_alias():
    cand = _candidate(primary_name="Ivan Petrov", aliases=[{"name": "Vanya Petrov"}])
    _, name = name_similarity("Vanya Petrov", cand)
    assert name == "Vanya Petrov"


def test_score_plain_name_only():
    cand = _candidate(identifiers=[], countries=[], dates_of_birth=[], aliases=[], entity_type=None)
    s = score_candidate(Query(name="Ivan Petrov"), cand)
    assert s.score == 100.0
    assert s.reason_codes == ("NAME_SIMILARITY",)


def test_score_identifier_match_dominates_weak_name():
    q = Query(name="Wrong Name Entirely", identifier="kz-123456")
    s = score_candidate(q, _candidate())
    assert s.identifier_match is True
    assert s.score >= 99.5
    assert "EXACT_IDENTIFIER" in s.reason_codes


def test_score_secondary_signal_bonuses():
    q = Query(name="Ivan Petrov", country="kazakhstan", date_of_birth="1975", entity_type="individual")
    s = score_candidate(q, _candidate(identifiers=[]))
    assert s.country_match and s.dob_match and s.entity_type_match
    assert {"COUNTRY_MATCH", "DOB_MATCH", "ENTITY_TYPE_MATCH"} <= set(s.reason_codes)
    assert s.score == 100.0


def test_score_alias_hit_is_flagged():
    s = score_candidate(Query(name="Ivan Petroff"), _candidate())
    assert s.matched_name == "Ivan Petroff"
    assert "ALIAS_MATCH" in s.reason_codes


def test_classify_no_candidates():
    assert classify([], 80, 95, True) == ("NO_MATCH", ("BELOW_REVIEW_THRESHOLD",))


def test_classify_below_review_threshold():
    outcome, _ = classify([_scored(70)], 80, 95, True)
    assert outcome == "NO_MATCH"


def test_classify_clear_match():
    scored = [_scored(98, identifier_match=True), _scored(60)]
    assert classify(scored, 80, 95, True) == ("MATCH", ("ABOVE_MATCH_THRESHOLD",))


def test_classify_match_needs_secondary_signal():
    scored = [_scored(98), _scored(60)]
    outcome, reasons = classify(scored, 80, 95, True)
    assert outcome == "POSSIBLE_MATCH"
    assert reasons == ("SECONDARY_IDENTIFIER_REQUIRED",)


def test_classify_match_when_secondary_not_required():
    scored = [_scored(98), _scored(60)]
    outcome, _ = classify(scored, 80, 95, False)
    assert outcome == "MATCH"


def test_classify_ambiguous_top_pair_goes_to_review():
    scored = [_scored(98, identifier_match=True), _scored(96, identifier_match=True)]
    outcome, reasons = classify(scored, 80, 95, True)
    assert outcome == "POSSIBLE_MATCH"
    assert "AMBIGUOUS_TOP_CANDIDATES" in reasons


def test_classify_review_band():
    outcome, reasons = classify([_scored(85), _scored(50)], 80, 95, True)
    assert outcome == "POSSIBLE_MATCH"
    assert "REVIEW_REQUIRED" in reasons
