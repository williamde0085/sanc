import re
import unicodedata

from unidecode import unidecode

# правовые формы - выкидываем из названий компаний
LEGAL_SUFFIXES = {"LLC", "LTD", "INC", "CORP", "GMBH", "AG", "OOO", "AO", "ZAO"}
STOP_WORDS = {"THE", "OF", "AND"}


def normalize_name(value):
    if not value or not value.strip():
        return ""
    text = unidecode(unicodedata.normalize("NFKC", value)).upper()
    tokens = re.sub(r"[^A-Z0-9]+", " ", text).split()
    kept = [t for t in tokens if t not in LEGAL_SUFFIXES and t not in STOP_WORDS]
    return " ".join(kept or tokens)


def normalize_identifier(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"[^A-Za-z0-9]", "", value).upper()
    return cleaned or None


def parse_year_or_date(value):
    v = value.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", v)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    if re.match(r"^\d{4}$", v):
        return int(v), None, None
    return None
