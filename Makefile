.PHONY: up down load test lint

up:
	docker compose up -d --build

down:
	docker compose down

load:
	python load_sanctions.py

test:
	pytest

lint:
	ruff check .
