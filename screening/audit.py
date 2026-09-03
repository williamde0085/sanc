import uuid
from datetime import UTC, datetime

from psycopg.types.json import Jsonb

from screening.hashing import chained_hash


def _iso(dt):
    # к UTC и всегда с микросекундами, иначе строка на записи и на проверке разъедется
    return dt.astimezone(UTC).isoformat(timespec="microseconds")


def _decision_event(d):
    # ровно этот dict хешируется. verify_chains собирает такой же из строки БД
    return {
        "decision_id": str(d["decision_id"]),
        "request_id": d["request_id"],
        "requested_at": _iso(d["requested_at"]),
        "normalized_query": d["normalized_query"],
        "list_version": d["list_version"],
        "matcher_version": d["matcher_version"],
        "outcome": d["outcome"],
        "top_score": float(d["top_score"]) if d["top_score"] is not None else None,
        "reason_codes": list(d["reason_codes"] or []),
        "candidates": list(d["candidates"] or []),
    }


def _review_event(r):
    return {
        "review_id": str(r["review_id"]),
        "decision_id": str(r["decision_id"]),
        "reviewer": r["reviewer"],
        "reviewed_at": _iso(r["reviewed_at"]),
        "outcome": r["outcome"],
        "notes": r["notes"],
    }


def record_decision(conn, request_id, normalized_query, list_version, matcher_version, outcome,
                    top_score, reason_codes, candidates, enqueue_review):
    decision_id = uuid.uuid4()
    requested_at = datetime.now(UTC)
    reason_codes = list(reason_codes)
    with conn.cursor() as cur:
        cur.execute("select event_hash from audit_chain_head where chain_name = 'decisions' for update")
        prev = cur.fetchone()["event_hash"]

        d = {
            "decision_id": decision_id, "request_id": request_id, "requested_at": requested_at,
            "normalized_query": normalized_query, "list_version": list_version,
            "matcher_version": matcher_version, "outcome": outcome,
            "top_score": top_score, "reason_codes": reason_codes, "candidates": candidates,
        }
        event_hash = chained_hash(prev, _decision_event(d))

        cur.execute(
            """
            insert into screening_decisions
              (decision_id, request_id, requested_at, normalized_query, list_version, matcher_version,
               outcome, top_score, reason_codes, candidates, previous_hash, event_hash)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (decision_id, request_id, requested_at, normalized_query, list_version, matcher_version,
             outcome, top_score, reason_codes, Jsonb(candidates), prev, event_hash),
        )
        cur.execute(
            "update audit_chain_head set event_hash = %s where chain_name = 'decisions'", (event_hash,)
        )
        if enqueue_review:
            cur.execute("insert into review_queue (decision_id) values (%s)", (decision_id,))
    conn.commit()
    return str(decision_id)


def record_review(conn, decision_id, reviewer, outcome,notes):
    reviewed_at = datetime.now(UTC)
    review_id = uuid.uuid4()
    with conn.cursor() as cur:
        cur.execute(
            """
            update screening_decisions
               set reviewer = %s, reviewed_at = %s, review_outcome = %s, review_notes = %s
             where decision_id = %s and reviewed_at is null
            """,
            (reviewer, reviewed_at, outcome, notes, decision_id),
        )
        if cur.rowcount != 1:
            conn.rollback()
            return False   # решения нет или уже отревьюено

        cur.execute("select event_hash from audit_chain_head where chain_name = 'reviews' for update")
        prev = cur.fetchone()["event_hash"]

        r = {
            "review_id": review_id, "decision_id": decision_id, "reviewer": reviewer,
            "reviewed_at": reviewed_at, "outcome": outcome, "notes": notes,
        }
        event_hash = chained_hash(prev, _review_event(r))

        cur.execute(
            """
            insert into review_events
              (review_id, decision_id, reviewer, reviewed_at, outcome, notes, previous_hash, event_hash)
            values (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (review_id, decision_id, reviewer, reviewed_at, outcome, notes, prev, event_hash),
        )
        cur.execute("update audit_chain_head set event_hash = %s where chain_name = 'reviews'", (event_hash,))
        cur.execute("update review_queue set status = 'closed' where decision_id = %s", (decision_id,))
    conn.commit()
    return True


def _check_chain(label, rows, events, head):
    errors =[]
    prev =None
    for row, event in zip(rows, events, strict=True):
        expected = chained_hash(prev, event)
        if row["previous_hash"] != prev or row["event_hash"] != expected:
            errors.append(f"{label}: звено не сходится")
        prev = row["event_hash"]
    if head != prev:
        errors.append(f"{label}: голова цепочки не сходится")
    return errors


def verify_chains(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            select decision_id, request_id, requested_at, normalized_query, list_version,
                   matcher_version, outcome, top_score, reason_codes, candidates,
                   previous_hash, event_hash
            from screening_decisions order by seq
            """
        )
        decisions = cur.fetchall()
        cur.execute(
            """
            select review_id, decision_id, reviewer, reviewed_at, outcome, notes,
                   previous_hash, event_hash
            from review_events order by seq
            """
        )
        reviews = cur.fetchall()
        cur.execute("select chain_name, event_hash from audit_chain_head")
        heads = {row["chain_name"]: row["event_hash"] for row in cur.fetchall()}

    d_events = []
    for row in decisions:
        d_events.append(_decision_event(row))
    r_events = []
    for row in reviews:
        r_events.append(_review_event(row))

    errors = _check_chain("decisions", decisions, d_events, heads.get("decisions"))
    errors += _check_chain("reviews", reviews, r_events, heads.get("reviews"))
    return {"valid": not errors, "errors": errors}
