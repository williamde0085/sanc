from screening.ofac import parse_xml


def test_parse_xml():
    recs = parse_xml("tests/fixtures/ofac_sample.xml")
    assert len(recs) == 2  # третья запись без имени
    assert recs[0]["entity_id"] == "SDN:1001"
    assert recs[0]["primary_name"] == "Ivan Petrov"
    assert recs[0]["aliases"][0]["name"] == "Иван Петров"
    assert recs[0]["identifiers"][0]["number"] == "KZ123456"
    assert "Kazakhstan" in recs[0]["countries"]
    assert recs[1]["primary_name"] == "ACME TRADING LLC"


def test_source_list():
    recs = parse_xml("tests/fixtures/ofac_sample.xml", source_list="CONSOLIDATED")
    assert recs[0]["entity_id"] == "CONSOLIDATED:1001"
