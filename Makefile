.PHONY: infra api web migrate admin test lint openapi

infra:            ## Sobe Postgres, Redis e Mailpit
	docker compose up -d db redis mailpit

api:              ## API em modo dev (http://localhost:8000/docs)
	cd backend && uv run alembic upgrade head && uv run uvicorn app.main:app --reload

web:              ## Frontend em modo dev (http://localhost:3000)
	cd frontend && pnpm dev

migrate:          ## Aplica as migrations
	cd backend && uv run alembic upgrade head

admin:            ## Cria um administrador: make admin EMAIL=voce@exemplo.com
	cd backend && uv run python -m app.cli create-admin $(EMAIL)

test:             ## Testes do backend
	cd backend && uv run pytest

lint:             ## Lint e checagem de tipos (backend e frontend)
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && pnpm lint && pnpm typecheck

openapi:          ## Exporta o contrato OpenAPI e regenera o cliente do frontend
	cd backend && uv run python -m app.cli export-openapi
	cd frontend && pnpm api:generate
