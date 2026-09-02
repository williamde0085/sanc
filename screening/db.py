from collections.abc import Iterator
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from screening.config import SERVING_DSN
from screening.models import Candidate


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    with psycopg.connect(SERVING_DSN, row_factory=dict_row, connect_timeout=5) as conn:
        yield conn


def find_candidates(conn, normalized_name, limit):
    if not normalized_name:
        return []
    sql = """
        select entity_id, primary_name, normalized_name, source_list, entity_type,
               programs, countries, dates_of_birth, identifiers, aliases, source_version
        from sanction_entries
        where normalized_name %% %s
        order by similarity(normalized_name, %s) desc
        limit %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (normalized_name, normalized_name, limit))
        rows = cur.fetchall()
    # колонки в select те же, что поля Candidate
    return [Candidate(**r) for r in rows]


def current_list_version(conn):
    sql = "select string_agg(distinct source_list || ':' || source_version, ',') as v from sanction_entries"
    with conn.cursor() as cur:
        cur.execute(sql)
        row = cur.fetchone()
    return row["v"] or "empty"


def get_decision(conn, decision_id):
    with conn.cursor() as cur:
        cur.execute("select * from screening_decisions where decision_id = %s", (decision_id,))
        return cur.fetchone()
