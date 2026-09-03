"""Prometheus-метрики. Отдаются на GET /metrics, скрейпятся Prometheus'ом."""

from prometheus_client import Counter, Histogram

screen_requests_total = Counter(
    "screening_screen_requests_total",
    "Запросы на POST /v1/screen в разбивке по исходу",
    ["outcome"],
)

screen_latency_seconds = Histogram(
    "screening_screen_latency_seconds",
    "Латентность обработки POST /v1/screen",
)

screen_candidates = Histogram(
    "screening_screen_candidates",
    "Сколько кандидатов выше порога ревью вернул один запрос",
    buckets=(0, 1, 2, 3, 5, 10, 25, 50),
)

audit_verify_failures_total = Counter(
    "screening_audit_verify_failures_total",
    "Сколько раз GET /v1/audit/verify обнаружил разрыв hash-chain",
)
