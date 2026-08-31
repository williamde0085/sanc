import hashlib
import json


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json_hash(value):
    # sort_keys обязателен, иначе хеш зависит от порядка ключей
    blob = json.dumps(value, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


def chained_hash(previous_hash, event):
    return stable_json_hash({"previous_hash": previous_hash or "", "event": event})
