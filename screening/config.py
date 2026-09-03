import os


def _flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes")


SERVING_DSN = os.getenv("SERVING_DSN", "postgresql://postgres:postgres@localhost:5432/sanctions")

API_KEY = os.getenv("SCREENING_API_KEY", "")

# пороги на глаз, потом настроить
REVIEW_THRESHOLD = float(os.getenv("SCREENING_REVIEW_THRESHOLD", "80"))
MATCH_THRESHOLD = float(os.getenv("SCREENING_MATCH_THRESHOLD", "95"))
REQUIRE_SECONDARY = _flag("SCREENING_REQUIRE_SECONDARY", True)

MAX_CANDIDATES = int(os.getenv("SCREENING_MAX_CANDIDATES", "50"))

OFAC_SDN_URL = os.getenv("OFAC_SDN_URL", "")
OFAC_CONSOLIDATED_URL = os.getenv("OFAC_CONSOLIDATED_URL", "")
DATA_DIR = os.getenv("DATA_DIR", "data")
