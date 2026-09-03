from fastapi.testclient import TestClient

from screening.api import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_screen_needs_api_key():
    r = client.post("/v1/screen", json={"name": "Vladimir Putin"})
    assert r.status_code == 401
