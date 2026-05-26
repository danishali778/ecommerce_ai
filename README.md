# CommerceOps AI

CommerceOps AI is a backend-first commerce operations platform for Shopify stores. It combines deterministic operational workflows with AI-assisted drafting, review, and execution so operators can move faster without giving up control over store changes.

Today the project covers two active product layers:

- `P0`: Shopify connection, sync, product content drafting, approvals, publish-back, auditability, and notifications
- `P1`: support conversations, policy-backed support drafts, fraud scoring, low-stock and reorder flows, and expanded analytics

## Why This Product Exists

Commerce teams lose time switching between store admin pages, spreadsheets, ad hoc support replies, and manual operational reviews. CommerceOps AI is designed to centralize those workflows into one operator system that can:

- import store data from Shopify
- generate AI-assisted content and operational drafts
- keep risky or sensitive actions behind human review
- log workflow, agent, approval, and audit activity
- build toward a more autonomous agentic operations layer over time

The product is intentionally not "auto-run everything" software. The current architecture emphasizes trust, traceability, and safe human supervision before deeper autonomy.

## Current Product Scope

### P0 Capabilities

- Shopify OAuth store connection
- manual and scheduled sync runs
- product catalog browsing
- AI product content draft generation
- draft preview and edit flow
- approval queue for publish-governed actions
- publish approved content back to Shopify
- workflow run, agent run, and audit visibility
- in-app notifications

### P1 Capabilities

- support conversation workspace
- support message logging
- policy document CRUD
- chunked policy retrieval with embedding-backed indexing
- AI support reply draft generation with citations and review flags
- deterministic fraud scoring and risk review queue
- low-stock alerts
- reorder suggestions and supplier reorder drafts
- expanded analytics endpoints

## Safety Model

CommerceOps AI is built around explicit operational guardrails:

- AI generation does not automatically imply store execution
- product content publishing remains approval-controlled
- support drafts stay internal and are not auto-sent to customers
- supplier reorder communication stays draft-only
- fraud decisions are recorded for review, not auto-executed against Shopify
- audit and workflow records are written for important system actions

## Architecture At A Glance

The active implementation is centered in `apps/api`.

- `api`: FastAPI transport layer and request/response schemas
- `services`: request-level orchestration
- `modules`: business-domain logic
- `repositories`: persistence and query logic
- `agents`: AI prompt, structured output, and LangGraph-based runners
- `tasks`: Celery background execution
- `integrations`: Shopify and external service adapters

Runtime stack:

- `api`: FastAPI app
- `worker`: Celery worker
- `beat`: Celery beat scheduler
- `redis`: queue broker

External dependencies:

- Supabase-hosted Postgres/Auth
- Shopify Admin APIs
- LLM provider for generation and embeddings

## Monorepo Layout

```text
apps/
  api/        FastAPI + Celery backend
  web/        frontend scaffold / future UI surface
docs/         architecture, schema, API, and planning docs
infra/        Docker and environment files
Releases/     phased release definitions
```

## Agent Layer

The repo already uses LangGraph, but in a deliberately lightweight way.

- current agent runners are mostly single-flow structured generation pipelines
- they assemble state, call the model, validate output, and persist workflow/agent records
- they are designed to evolve into richer multi-node agent workflows later

Current named agents include:

- `Product Content Agent`
- `Support Agent`
- future-facing domain agent patterns for inventory, fraud/risk, pricing, and analytics

## Local Development

### Prerequisites

- Python `3.12+`
- Docker Desktop
- a reachable Supabase project
- Shopify app credentials
- LLM provider credentials

### Environment

This repo expects an environment file at:

```text
infra/env/.env
```

At a minimum, the backend expects values for:

- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SHOPIFY_API_KEY`
- `SHOPIFY_API_SECRET`
- `SHOPIFY_SCOPES`
- `SHOPIFY_APP_URL`
- `SHOPIFY_REDIRECT_URL`
- `OPENAI_API_KEY` or your configured LLM provider credentials

Supabase is external in local development. Docker Compose does not run Postgres/Auth locally for this project.

### Start The Stack

From the repo root:

```powershell
docker compose up -d redis api worker beat
```

The backend will be available at:

```text
http://localhost:8000
```

Swagger docs:

```text
http://localhost:8000/docs
```

### Common Local Commands

Watch logs:

```powershell
docker compose logs -f api worker beat
```

Rebuild containers:

```powershell
docker compose up --build -d redis api worker beat
```

Stop services:

```powershell
docker compose down
```

## Database And Migrations

The backend uses SQLAlchemy models plus SQL migrations under:

```text
apps/api/alembic/versions/
```

Phase 1 introduced additional operator schema for:

- support conversations and messages
- policy documents and chunks
- inventory alerts and reorder suggestions
- supplier reorder drafts
- risk reviews

When bringing up a fresh environment, make sure the database schema is up to date before testing the API and worker flows.

## Testing

Primary backend regression command:

```powershell
venv\Scripts\python.exe -m pytest apps/api/tests/unit apps/api/tests/api/test_backend_routes.py apps/api/tests/contract/test_openapi_snapshot.py -q
```

The current backend test surface includes:

- unit tests for domain logic
- API route registration and behavior coverage
- OpenAPI snapshot coverage
- live manual verification through Swagger and real Shopify-connected flows

## Typical Operator Flows

### Product Content Flow

1. connect store
2. run sync
3. browse products
4. generate content draft
5. review and submit for approval
6. approve
7. publish back to Shopify

### Support Flow

1. create support conversation
2. log inbound message
3. retrieve policy context
4. generate support draft
5. review low-confidence or sensitive drafts
6. manually send outside the platform

### Operations Intelligence Flow

1. sync commerce data
2. evaluate fraud scores on imported orders
3. evaluate inventory thresholds on variants
4. create risk reviews, alerts, and reorder suggestions
5. inspect results through analytics and domain endpoints

## Current Limitations

- `apps/web` is not yet a production UI surface
- support is internal-console-only in the current product phase
- draft orders are not treated as the same thing as real Shopify orders for fraud workflows
- direct autonomous customer messaging and supplier outreach are intentionally out of scope
- multi-store and enterprise expansion are deferred to later phases

## Documentation

- [Public Architecture Overview](docs/public/architecture.md)
- [Public API Design Overview](docs/public/api-design.md)
- [Public Schema Design Overview](docs/public/schema-design.md)
- [Public Agents Layer Overview](docs/public/agents-layer.md)

## Roadmap Direction

The longer-term goal is to evolve from AI-assisted operator tooling into richer autonomous commerce operations, but in phases:

- `P0`: safe execution foundation
- `P1`: supervised operational intelligence
- `P2`: deeper automation, pricing, and workflow evolution
- later: more agentic orchestration, broader channels, and enterprise capabilities

That means the current backend already lays the groundwork for agents, workflows, auditability, and approvals without skipping straight to unsafe autonomy.
