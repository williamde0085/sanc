from screening.normalize import normalize_identifier, normalize_name, parse_year_or_date


def test_empty_and_blank():
    assert normalize_name("") == ""
    assert normalize_name("   ") == ""
    assert normalize_name(None) == ""


def test_uppercase_and_punctuation():
    assert normalize_name("Al-Qaeda") == "AL QAEDA"
    assert normalize_name("john   q.  public") == "JOHN Q PUBLIC"


def test_transliteration_cyrillic():
    assert normalize_name("Иван Петров") == "IVAN PETROV"


def test_legal_suffixes_dropped():
    assert normalize_name("ACME Trading LLC") == "ACME TRADING"
    assert normalize_name("Kopyta OOO") == "KOPYTA"


def test_stop_words_dropped():
    assert normalize_name("The Bank of Moscow") == "BANK MOSCOW"


def test_all_tokens_stripped_falls_back_to_original():
    # если после чистки не осталось ни одного токена - возвращаем что было, а не пустую строку
    assert normalize_name("LLC") == "LLC"
    assert normalize_name("The") == "THE"


def test_normalize_identifier():
    assert normalize_identifier(None) is None
    assert normalize_identifier("") is None
    assert normalize_identifier("!!!") is None
    assert normalize_identifier("kz-12 34/56") == "KZ123456"


def test_parse_year_only():
    assert parse_year_or_date("1975") == (1975, None, None)
    assert parse_year_or_date("  1980 ") == (1980, None, None)


def test_parse_full_iso_date():
    assert parse_year_or_date("1975-06-01") == (1975, 6, 1)


def test_parse_dirty_dob_rejected():
    assert parse_year_or_date("circa 1975") is None
    assert parse_year_or_date("1970 to 1975") is None
    assert parse_year_or_date("") is None
