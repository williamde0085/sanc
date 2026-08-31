def record_decision(conn, request_id, normalized_query, list_version, outcome,
                    top_score, reason_codes, candidates, enqueue_review):
    # голову цепочки читаем под SELECT ... FOR UPDATE, потом INSERT + UPDATE audit_chain_head
    raise NotImplementedError


def record_review(conn, decision_id, reviewer, outcome, notes):
    raise NotImplementedError


def verify_chains(conn):
    raise NotImplementedError
