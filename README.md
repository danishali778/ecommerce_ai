# CommerceOps AI

CommerceOps AI is a commerce operations platform for Shopify stores. It combines deterministic operational workflows with AI-assisted drafting, review, and execution so operators can move faster without giving up control over store changes.

Today the repo includes four implemented platform layers:

- `P0`: Shopify connection, sync, product content drafting, approvals, publish-back, auditability, and notifications
- `P1`: support conversations, policy-backed support drafts, fraud scoring, low-stock and reorder flows, and expanded analytics
- `P2`: pricing rules, price simulations and recommendations, user-authored workflows, and external notification channels
- `P3`: runtime hardening for retries, failure classification, traceability, delivery recovery, and agent/worker regression coverage

## Why This Product Exists

Commerce teams lose time switching between store admin pages, spreadsheets, ad hoc support replies, and manual operational reviews. CommerceOps AI is designed to centralize those workflows into one operator system that can:

- import store data from Shopify
- generate AI-assisted content and operational drafts
- keep risky or sensitive actions behind human review
- log workflow, agent, approval, and audit activity
- build toward a more autonomous agentic operations layer over time

The product is intentionally not "auto-run everything" software. The current architecture emphasizes trust, traceability, and safe human supervision before deeper autonomy.

## Current Product Scope And Status

### Implementation Status

- backend: active and implemented through `P3`
- frontend: active React/Vite operator console in `apps/web`
- database: requires the latest SQL migrations in `apps/api/alembic/versions`
- workers: Celery + Redis based async execution for sync, approvals, agents, workflows, and notifications

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
- agent-backed fraud/risk assessment and risk review queue
- low-stock alerts
- agent-backed reorder suggestions and supplier reorder drafts
- expanded analytics endpoints

### P2 Capabilities

- pricing rule CRUD
- manual reference-price entry
- CSV reference-price import
- agent-backed pricing simulation
- agent-backed persisted pricing recommendations
- pricing approvals through the existing approval system
- user-authored workflow definitions
- workflow enable, disable, update, delete, and dry-run testing
- external notification channels:
  - webhook
  - email
- notification preferences and delivery records
- pricing, workflow, and notification analytics extensions

### P3 Hardening Capabilities

- shared runtime failure taxonomy:
  - `transient`
  - `permanent`
  - `requires_operator`
- trace propagation from API request to worker/runtime records
- standardized retry settings per flow
- persisted async attempt history via `job_attempts`
- workflow-run retry API
- notification-delivery list, detail, and retry APIs
- runtime metadata on sync runs, workflow runs, agent runs, approvals, and deliveries
- operational analytics for retries, queue lag, failure counts, and runtime latency
- deterministic agent regression coverage plus optional live agent evals

## Safety Model

CommerceOps AI is built around explicit operational guardrails:

- AI generation does not automatically imply store execution
- product content publishing remains approval-controlled
- support drafts stay internal and are not auto-sent to customers
- supplier reorder communication stays draft-only
- fraud decisions are recorded for review, not auto-executed against Shopify
- pricing recommendations are not auto-published to Shopify
- audit and workflow records are written for important system actions

## Architecture At A Glance

The active implementation is centered in `apps/api`, with the operator UI in `apps/web`.

- `api`: FastAPI transport layer and request/response schemas
- `services`: request-level orchestration
- `modules`: business-domain logic
- `repositories`: persistence and query logic
- `agents`: AI prompt, structured output, and LangGraph-based runners
- `tasks`: Celery background execution
- `integrations`: Shopify and external service adapters
- `web`: Vite + React + TypeScript frontend

Runtime stack:

- `api`: FastAPI app
- `worker`: Celery worker
- `beat`: Celery beat scheduler
- `redis`: queue broker
- `web`: Vite development server / static production bundle

External dependencies:

- Supabase-hosted Postgres/Auth
- Shopify Admin APIs
- LLM provider for generation and embeddings

## Monorepo Layout

```text
apps/
  api/        FastAPI + Celery backend
  web/        React + Vite frontend
  video/      Remotion video workspace
docs/         architecture, schema, API, and planning docs
infra/        Docker and environment files
Releases/     phased release definitions
```

## Agent Layer

The repo already uses LangGraph, but in a deliberately lightweight way.

- current agent runners are mostly single-flow structured generation pipelines
- they assemble state, call the model, validate output, and persist workflow/agent records
- they are designed to evolve into richer multi-node agent workflows later

Current implemented agents include:

- `Product Content Agent`
- `Support Agent`
- inventory
- fraud/risk
- pricing

Planned future agent families are still documented for:

- analytics

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

Frontend local development also expects the API to be reachable from the browser, normally at:

```text
http://localhost:8000/api/v1
```

If you are using the local frontend in `apps/web`, make sure the backend CORS settings allow your frontend origin, for example `http://localhost:5173`.

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

### Start The Frontend

From the repo root:

```powershell
npm install
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

Other frontend commands:

```powershell
npm run build
npm run test
npm run preview
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

The repo now includes schema extensions for:

- `P1`:
  - support conversations and messages
  - policy documents and chunks
  - inventory alerts and reorder suggestions
  - supplier reorder drafts
  - risk reviews
- `P2`:
  - pricing rules, reference inputs, and recommendations
  - workflow-definition fields
  - notification channels, preferences, and deliveries
- `P3`:
  - runtime hardening metadata on existing operational tables
  - `job_attempts`

When bringing up a fresh environment, make sure the database schema is up to date before testing the API and worker flows.

Important recent migrations:

- [20260607_005_add_commerce_ops_p2_backend_schema.sql](apps/api/alembic/versions/20260607_005_add_commerce_ops_p2_backend_schema.sql)
- [20260608_006_add_commerce_ops_p3_runtime_hardening.sql](apps/api/alembic/versions/20260608_006_add_commerce_ops_p3_runtime_hardening.sql)
- [20260608_007_add_true_agent_fields_for_inventory_fraud_pricing.sql](apps/api/alembic/versions/20260608_007_add_true_agent_fields_for_inventory_fraud_pricing.sql)

## Testing

Primary backend regression command:

```powershell
venv\Scripts\python.exe -m pytest apps/api/tests/unit apps/api/tests/api/test_backend_routes.py apps/api/tests/contract/test_openapi_snapshot.py -q
```

The current backend test surface includes:

- unit tests for domain logic
- API route registration and behavior coverage
- OpenAPI snapshot coverage
- deterministic runtime and agent regression coverage
- optional live verification through Swagger and real Shopify-connected flows

Phase 3 non-live verification:

```powershell
venv\Scripts\python.exe -m compileall apps\api\app
venv\Scripts\python.exe -m pytest apps/api/tests -q -m "not live"
```

Optional live agent evals:

```powershell
$env:LIVE_ENABLE_AGENT_EVALS="1"
venv\Scripts\python.exe -m pytest apps/api/tests/live/test_live_agent_evals.py -q -m live
```

## Manual Validation Snapshot

Recent manual QA covered the main local operator flows with a real Shopify-connected store, active worker stack, and authenticated Swagger testing.

- full walkthrough: [Manual Testing Guide](docs/public/manual-testing.md)
- major flows validated: store connection, sync, content drafting, approvals, support, fraud, inventory, analytics, pricing, and workflows
- notable issues found during QA were fixed locally before re-testing, including inventory agent output handling and analytics automation metrics

### Sync Run Queued

![Queued sync run](assets/job-queued-to-pull-data-1.png)

### Generated Product Draft

![Generated product draft](assets/generated-draft-1.png)

### Support Reply Draft

![Generated support reply draft](assets/message-reply.png)

### Pricing Recommendation

![Pricing recommendation details](assets/pricing-recommendation-2.png)

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
2. create fraud/risk agent runs for imported orders
3. create inventory agent runs for below-threshold variants
4. create risk reviews, alerts, reorder suggestions, and supplier draft recommendations
5. inspect results through analytics and domain endpoints

## Current Limitations

- frontend and backend are active, but deployment hardening and broader production operations still need environment-specific rollout work
- support is internal-console-only in the current product phase
- draft orders are not treated as the same thing as real Shopify orders for fraud workflows
- direct autonomous customer messaging and supplier outreach are intentionally out of scope
- direct autonomous pricing publish is intentionally out of scope
- multi-store and enterprise expansion are deferred to later phases

## Documentation

- [Public Architecture Overview](docs/public/architecture.md)
- [Public API Design Overview](docs/public/api-design.md)
- [Public Schema Design Overview](docs/public/schema-design.md)
- [Public Agents Layer Overview](docs/public/agents-layer.md)
- [Manual Testing Guide](docs/public/manual-testing.md)
- [Phase 3 Runtime Hardening Rollout](docs/internal/Phase3_Runtime_Hardening_Rollout.md)

## Roadmap Direction

The longer-term goal is to evolve from AI-assisted operator tooling into richer autonomous commerce operations, but in phases:

- `P0`: safe execution foundation
- `P1`: supervised operational intelligence
- `P2`: pricing, workflow definitions, and external notification channels
- `P3`: platform hardening, runtime traceability, and retry safety
- later: more agentic orchestration, broader channels, and enterprise capabilities

That means the current backend already lays the groundwork for agents, workflows, auditability, and approvals without skipping straight to unsafe autonomy.
