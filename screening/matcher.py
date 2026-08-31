from screening.models import Candidate, Query, ScoredCandidate


def name_similarity(query_name, candidate):
    raise NotImplementedError


def score_candidate(query: Query, candidate: Candidate) -> ScoredCandidate:
    raise NotImplementedError


def classify(scored, review_threshold, match_threshold, require_secondary):
    raise NotImplementedError("дописать логику порогов")
