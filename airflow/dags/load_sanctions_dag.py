"""Опциональный Airflow DAG: ежедневно обновляет санкционные списки в БД.

Для локальной работы не нужен - есть `make load` / `python load_sanctions.py`.
Файл кладётся в dags-папку Airflow; OFAC_SDN_URL, OFAC_CONSOLIDATED_URL и
SERVING_DSN берутся из окружения воркера (см. .env.example).
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load() -> None:
    from load_sanctions import main

    rc = main()
    if rc != 0:
        raise RuntimeError(f"load_sanctions.main() вернул код {rc}")


default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="load_sanctions",
    description="Скачать SDN/Consolidated из OFAC и перезалить в sanction_entries",
    schedule="0 6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["sanctions", "etl"],
) as dag:
    PythonOperator(task_id="download_and_load", python_callable=_load)
