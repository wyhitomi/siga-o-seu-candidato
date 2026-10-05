# Frontend — Siga o seu candidato

Next.js (App Router) + TypeScript + Tailwind CSS.

```bash
cp .env.example .env.local
pnpm install
pnpm dev               # http://localhost:3000
pnpm api:generate      # regenera src/lib/api/schema.d.ts a partir de ../openapi/openapi.json
pnpm lint && pnpm typecheck
```

O cliente HTTP (`src/lib/api/client.ts`) é tipado a partir do contrato OpenAPI
da API; não edite `schema.d.ts` à mão.
