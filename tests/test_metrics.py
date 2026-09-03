from fastapi.testclient import TestClient

from screening.api import app

client = TestClient(app)


def test_metrics_endpoint_exposes_prometheus_text():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    # гистограмма без лейблов появляется в выдаче сразу
    assert "screening_screen_latency_seconds_bucket" in r.text
