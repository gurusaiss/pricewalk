.PHONY: dev down test lint migrate format

dev:
	docker compose -f infra/docker-compose.yml up --build

down:
	docker compose -f infra/docker-compose.yml down

test:
	pytest
	cd apps/web && npm run build

lint:
	ruff check .
	mypy packages/core services/api services/worker
	cd apps/web && npm run lint

format:
	ruff format .
	cd apps/web && npm run format

migrate:
	cd packages/core && alembic upgrade head

migration:
	cd packages/core && alembic revision --autogenerate -m "$(m)"
