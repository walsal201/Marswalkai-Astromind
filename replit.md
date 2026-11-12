# AstroMind Space Mission Suite

AstroMind is a demo-ready mission-planning suite for deep-space missions and Mars surface EVAs.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string
- AstroMind preview uses the managed `artifacts/astromind: web` and `artifacts/astromind: api` workflows.
- `pnpm --filter @workspace/astromind run typecheck` — typecheck AstroMind's Vite host.
- `PORT=22994 BASE_PATH=/ pnpm --filter @workspace/astromind run build` — build AstroMind's web host.
- AstroMind starts in Demo mode; optional CrewAI dependencies and provider credentials are documented in `artifacts/astromind/README.md`.

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- Shared API: Express 5; AstroMind API: FastAPI
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `artifacts/astromind/public/mission-console.html` — supplied mission console UI.
- `artifacts/astromind/main.py` — FastAPI routes and demo/live mode selection.
- `artifacts/astromind/demo_data.py` — orbital calculations and demo responses.
- `artifacts/astromind/crew_agents.py` — optional CrewAI agents.
- `artifacts/astromind/.replit-artifact/artifact.toml` — web and API service routing.
- `lib/api-spec/openapi.yaml` — shared Express API contract.

## Architecture decisions

- AstroMind keeps the supplied HTML console and displays it through the Vite app host.
- AstroMind API requests use `/astro-api` so they do not collide with the shared `/api` Express service.
- Demo mode is the default and requires no provider credentials; CrewAI is optional.

## Product

- Deep-space mission profiles, trajectory metrics, risk matrices, timelines, briefs, and chat.
- MarswalkAI route editing, synthetic terrain layers, science targets, weather, hazards, EVA plans, and checklists.
- Exportable planning output; all values are planning-level estimates.

## User preferences

_No additional project-specific preferences recorded._

## Gotchas

- The artifact's Vite config requires `PORT` and `BASE_PATH` for direct build commands.
- Keep AstroMind's API under `/astro-api`; `/api` is already routed to the shared Express service.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
