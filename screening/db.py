from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from screening.config import SERVING_DSN


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    with psycopg.connect(SERVING_DSN, row_factory=dict_row, connect_timeout=5) as conn:
        yield conn


def find_candidates(conn, normalized_name, limit):
    # pg_trgm: similarity(normalized_name, %s) + отсечка по порогу, order by desc limit
    raise NotImplementedError


def current_list_version(conn):
    pass


def get_decision(conn, decision_id):
    raise NotImplementedError
