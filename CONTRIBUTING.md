# Como contribuir

## Fluxo de trabalho

1. Toda mudança começa por uma **issue** e, se alterar comportamento, por uma
   **spec ou change em `openspec/`**.
2. Crie uma branch a partir de `main` (`feat/busca-senadores`, `fix/cache-ttl`).
3. Abra **PRs curtos**: um assunto por PR, idealmente até ~400 linhas de diff
   (sem contar arquivos gerados). Se crescer, quebre em PRs encadeados.
4. O PR precisa de revisão antes do merge. Use *squash merge* para que o título
   do PR vire o commit em `main`.

## Conventional Commits

Commits e títulos de PR seguem [Conventional Commits](https://www.conventionalcommits.org/pt-br/):

```
<tipo>(<escopo opcional>): <descrição no imperativo>
```

| Tipo | Quando usar |
|---|---|
| `feat` | Nova funcionalidade para o usuário |
| `fix` | Correção de bug |
| `docs` | Somente documentação |
| `refactor` | Mudança de código sem alterar comportamento |
| `test` | Testes |
| `build` | Dependências, Docker, empacotamento |
| `ci` | Pipelines |
| `chore` | Manutenção que não se encaixa acima |

Escopos usados: `api`, `web`, `auth`, `connectors`, `db`, `openspec`, `deps`.
Mudanças incompatíveis usam `!` (`feat(api)!: ...`) e um rodapé `BREAKING CHANGE:`.
O título do PR é validado no CI, porque ele vira o commit em `main`.

## CI

Todo PR roda `.github/workflows/ci.yml`: lint e testes do backend, migrations
num Postgres real (`upgrade`, `check` e `downgrade`), lint/typecheck/build do
frontend, verificação do contrato OpenAPI e build das imagens Docker. Só roda o
que foi afetado pelo diff. O check obrigatório é o `ci-ok`, que agrega todos.

## Releases

As releases são automáticas via [release-please](https://github.com/googleapis/release-please):

1. A cada merge em `main`, o release-please abre ou atualiza um PR
   `chore: release main` com a próxima versão e o CHANGELOG de cada pacote
   (`backend` e `frontend`), calculados a partir dos commits.
2. Ao fazer merge desse PR, são criadas as tags (`backend-vX.Y.Z`,
   `frontend-vX.Y.Z`) e as GitHub Releases.

Antes da 1.0: `feat` e mudanças incompatíveis (`!`/`BREAKING CHANGE`) sobem a
versão minor (0.**2**.0); `fix` e `perf` sobem a patch (0.1.**1**). `docs`,
`test`, `ci`, `build` e `chore` não geram release sozinhos.

## Boas práticas

- **Contrato primeiro**: a API é a fonte da verdade. Depois de mudar rotas ou
  schemas, rode `make openapi` e comite `openapi/openapi.json`; o cliente do
  frontend é gerado a partir dele.
- **Testes**: toda feature ou fix vem com teste. Conectores de fontes públicas
  são testados com fixtures, sem rede.
- **Lint e formatação**: `make lint` (ruff no backend, eslint + tsc no frontend).
- **Segredos** nunca entram no repositório; use `.env` (veja `.env.example`).
- **LGPD**: o acesso público é anônimo. Não registre IPs em claro, não guarde
  CPF, título de eleitor, data de nascimento ou e-mail pessoal de candidatos, e
  não adicione rastreadores de terceiros.
