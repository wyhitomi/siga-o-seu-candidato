# siga-o-seu-candidato

Siga o seu candidato é uma aplicação para ajudar pessoas a saberem o que seus
candidatos estão fazendo depois de eleitos, usando dados públicos do governo.
O acesso é **anônimo** (sem cadastro e sem rastreamento); apenas
administradores fazem login.

## O que já funciona

| Funcionalidade | Onde | Fonte de dados |
|---|---|---|
| Busca de senadores em exercício | `/senadores`, `GET /api/v1/senators` | Dados Abertos do Senado |
| Busca de deputados estaduais e distritais eleitos | `/deputados-estaduais`, `GET /api/v1/state-deputies` | TSE Dados Abertos (eleição 2022) |
| Login de administradores por link no e-mail | `/admin/login`, `POST /api/v1/auth/*` | — |
| Carga de dados sob demanda (admin) | `/admin`, `POST /api/v1/admin/sync/*` | — |

## Arquitetura

```
Navegador ─► Next.js (SSR) ─► FastAPI ─► Redis (cache) ─► PostgreSQL ─► Conectores (Senado, TSE…)
```

- `backend/`: FastAPI + SQLAlchemy async + Alembic. Os módulos de domínio ficam em
  `app/modules`, e há uma integração por fonte em `app/connectors`.
- `frontend/`: Next.js + Tailwind, com cliente tipado gerado do OpenAPI.
- `openapi/openapi.json`: contrato da API, versionado.
- `openspec/`: especificações das funcionalidades (spec-driven development).

## Rodando localmente

Pré-requisitos: Docker, [uv](https://docs.astral.sh/uv/) e pnpm.

```bash
make infra                         # Postgres, Redis e Mailpit
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
(cd backend && uv sync) && (cd frontend && pnpm install)

make admin EMAIL=voce@exemplo.com  # cria o primeiro administrador
make api                           # http://localhost:8000/docs
make web                           # http://localhost:3000
```

Os e-mails de login chegam no Mailpit (http://localhost:8025). Para subir tudo
em contêineres, use `docker compose up --build`.

Os senadores são carregados automaticamente na primeira busca. Os deputados
estaduais vêm de um arquivo grande do TSE e são carregados pelo painel `/admin`.

## Desenvolvimento

```bash
make test      # testes do backend
make lint      # ruff + eslint + tsc
make openapi   # depois de mudar a API: exporta o contrato e regenera o cliente
```

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para o fluxo de trabalho (PRs curtos e
Conventional Commits).

## Privacidade (LGPD)

- Visitantes não fazem login, e o site não usa cookies nem rastreadores.
- A API em produção não grava IPs nos logs (`--no-access-log`).
- Só guardamos dados de interesse público dos agentes políticos. CPF, título de
  eleitor, data de nascimento e e-mail pessoal dos candidatos são descartados na
  carga.
