import json
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

NS = {"s": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML"}


def _name(el):
    first = el.findtext("s:firstName", "", NS).strip()
    last = el.findtext("s:lastName", "", NS).strip()
    return (first + " " + last).strip()


def parse_xml(path,source_list="SDN"):
    records = []
    for _, entry in ET.iterparse(path):
        if not entry.tag.endswith("}sdnEntry"):
            continue

        uid = entry.findtext("s:uid", "", NS).strip()
        name = _name(entry)
        if not uid or not name:
            entry.clear()
            continue

        programs = []
        for p in entry.findall("s:programList/s:program", NS):
            if p.text and p.text.strip():
                programs.append(p.text.strip())

        dob = []
        for d in entry.findall("s:dateOfBirthList/s:dateOfBirthItem/s:dateOfBirth", NS):
            if d.text and d.text.strip():
                dob.append(d.text.strip())

        countries = []
        for c in entry.iter():
            if c.tag.endswith("}country") and c.text and c.text.strip():
                countries.append(c.text.strip())

        aliases = []
        for aka in entry.findall("s:akaList/s:aka", NS):
            n = _name(aka)
            if n:
                aliases.append({"name": n, "type": aka.findtext("s:type", "", NS).strip()})

        ids = []
        for node in entry.findall("s:idList/s:id", NS):
            num = node.findtext("s:idNumber", "", NS).strip()
            if num:
                ids.append({"type": node.findtext("s:idType", "", NS).strip(), "number": num})

        records.append({
            "entity_id": f"{source_list}:{uid}",
            "source_list": source_list,
            "entity_type": entry.findtext("s:sdnType", "", NS).strip() or None,
            "primary_name": name,
            "programs": programs,
            "countries": list(dict.fromkeys(countries)),
            "dates_of_birth": dob,
            "aliases": aliases,
            "identifiers": ids,
        })
        entry.clear()  # без этого распарсенные записи копятся в памяти
    return records


def download(url, dest_dir):
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / url.rsplit("/", 1)[-1]
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def to_jsonl(records, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return len(records)
