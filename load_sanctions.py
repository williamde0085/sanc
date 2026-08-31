import os
import sys

from screening.config import DATA_DIR, OFAC_CONSOLIDATED_URL, OFAC_SDN_URL, SERVING_DSN

MIN_EXPECTED_RECORDS = 5000


def main():
    # download -> parse -> проверить кол-во записей -> TRUNCATE + INSERT
    raise NotImplementedError


if __name__ == "__main__":
    if not (SERVING_DSN and OFAC_SDN_URL and OFAC_CONSOLIDATED_URL):
        print("missing SERVING_DSN / OFAC_*_URL, check .env", file=sys.stderr)
        raise SystemExit(2)
    os.makedirs(DATA_DIR, exist_ok=True)
    raise SystemExit(main())
