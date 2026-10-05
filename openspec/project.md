# Project Context

## Purpose

**Siga o seu candidato** ajuda qualquer pessoa a acompanhar o que seus
representantes eleitos fazem depois da eleição, reunindo dados de bases
públicas (Senado, Assembleias Legislativas, TSE, Portal da Transparência,
Judiciário) em uma busca simples.

## Tech Stack

- Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic
- Banco: PostgreSQL 16 (`pg_trgm` para busca por nome)
- Cache: Redis 7 (cache-aside, versionado por fonte)
- Frontend: Next.js (App Router), TypeScript, Tailwind CSS
- Contrato: OpenAPI 3.1 gerado pelo FastAPI e versionado em `openapi/openapi.json`

## Project Conventions

### Code Style

- Python: ruff (lint + format), type hints obrigatórios em código novo.
- TypeScript: modo `strict`, eslint.
- Nomes de código em inglês; textos para o usuário em português do Brasil.

### Architecture Patterns

- Módulos por domínio em `backend/app/modules/<domínio>` (router, schemas,
  service, repository).
- Uma integração por fonte de dados em `backend/app/connectors/`, sem acesso a
  banco; o service decide quando consultar a fonte e persiste o resultado.
- Fluxo de leitura: Redis → PostgreSQL → fonte externa.

### Testing Strategy

- pytest + pytest-asyncio; banco SQLite em memória e Redis falso nos testes
  unitários; fixtures para respostas das fontes públicas (sem rede).

### Git Workflow

- PRs curtos, squash merge, Conventional Commits (veja `CONTRIBUTING.md`).

## Domain Context

- **Parlamentar**: pessoa em exercício de mandato legislativo. Nesta fase:
  senadores (Senado Federal) e deputados estaduais/distritais.
- Fontes atuais: API de Dados Abertos do Senado (senadores em exercício) e
  TSE Dados Abertos (candidaturas eleitas para deputado estadual/distrital).

## Important Constraints

- **LGPD**: acesso público anônimo, sem cadastro e sem rastreadores. Apenas
  administradores fazem login. Guardamos somente dados de interesse público
  dos agentes políticos (minimização).
- Fontes públicas podem ficar fora do ar: sempre servir o último dado
  persistido, informando a data da coleta.

## External Dependencies

- Senado Federal — https://legis.senado.leg.br/dadosabertos
- TSE Dados Abertos — https://dadosabertos.tse.jus.br
