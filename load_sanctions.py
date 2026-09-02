import os
import sys

import psycopg
from psycopg.types.json import Jsonb

from screening.config import DATA_DIR, OFAC_CONSOLIDATED_URL, OFAC_SDN_URL, SERVING_DSN
from screening.hashing import sha256_file
from screening.normalize import normalize_name
from screening.ofac import download, parse_xml

MIN_EXPECTED_RECORDS = 5000


def main():
    rows = []
    for name, url in [("SDN", OFAC_SDN_URL), ("CONSOLIDATED", OFAC_CONSOLIDATED_URL)]:
        print("downl", url)
        path = download(url, DATA_DIR)
        file_hash = sha256_file(path)
        for r in parse_xml(path, name):
            rows.append((
                r["entity_id"],
                r["source_list"],
                r["entity_type"],
                r["primary_name"],
                normalize_name(r["primary_name"]),
                r["programs"],
                sorted(set(r["countries"])),
                r["dates_of_birth"],
                Jsonb(r["identifiers"]),
                Jsonb(r["aliases"]),
                file_hash,
            ))

    if len(rows) < MIN_EXPECTED_RECORDS:
        raise RuntimeError(f"{len(rows)} записей, ждали >= {MIN_EXPECTED_RECORDS}, не гружу")

    sql = """
        insert into sanction_entries
          (entity_id, source_list, entity_type, primary_name, normalized_name,
           programs, countries, dates_of_birth, identifiers, aliases, source_version)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with psycopg.connect(SERVING_DSN) as conn, conn.cursor() as cur:
        cur.execute("truncate sanction_entries")
        cur.executemany(sql, rows)
        conn.commit()

    print(f"загружено {len(rows)} записей")
    return 0


if __name__ == "__main__":
    if not (SERVING_DSN and OFAC_SDN_URL and OFAC_CONSOLIDATED_URL):
        print("missing SERVING_DSN / OFAC_*_URL, check .env", file=sys.stderr)
        raise SystemExit(2)
    os.makedirs(DATA_DIR, exist_ok=True)
    raise SystemExit(main())
