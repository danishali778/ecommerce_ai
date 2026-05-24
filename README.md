# CommerceOps AI

CommerceOps AI is a backend-first `P0` monorepo for Shopify-connected operations workflows: store sync, AI draft generation, approval-controlled publishing, audit trails, and in-app notifications.

## Current scope

- `apps/api` contains the active FastAPI + Celery backend
- Shopify OAuth, sync, content drafts, approvals, workflow logs, and notifications are implemented in the backend
- `apps/web` is still scaffold-only, so browser E2E remains a tracked follow-up rather than a shippable part of `P0`

## Local runtime model

Docker Compose in this repo runs the application stack only:

- `api`
- `worker`
- `beat`
- `redis`

Supabase is **external** for local development. The project does not self-host Postgres/Auth locally through Compose, so `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` must point at a real Supabase environment before the app can boot.

## Backend quick start

1. Copy `.env.example` to `infra/env/.env`.
2. Fill in the external Supabase values and the Shopify / LLM credentials you want to use.
3. Install backend dependencies from `apps/api/pyproject.toml`.
4. Start the stack with Docker Compose or your preferred local commands for `api`, `worker`, and `beat`.
5. Run the backend tests from `apps/api/tests`.

## P0 testing note

The backend now covers API and worker journeys for `P0`. Browser E2E is intentionally deferred until `apps/web` becomes a real UI surface.

## Primary references

- [CommerceOps_AI_PRD.md](/d:/Projects/ecommerce_automation/CommerceOps_AI_PRD.md)
- [docs/CommerceOps_AI_Tech_Stack.md](/d:/Projects/ecommerce_automation/docs/CommerceOps_AI_Tech_Stack.md)
- [docs/CommerceOps_AI_Monorepo_Structure.md](/d:/Projects/ecommerce_automation/docs/CommerceOps_AI_Monorepo_Structure.md)
