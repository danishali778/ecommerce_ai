# CommerceOps AI - Architecture

CommerceOps AI is a backend-first Shopify operations system. The platform combines a FastAPI API, Celery workers, Shopify sync, internal workflow state, and AI-assisted drafting under a controlled approval model.

## System Context

```mermaid
graph TD
    OP[Operator] --> UI[Future Web UI / Swagger]
    UI --> API[FastAPI API]
    API --> AUTH[Supabase Auth]
    API --> DB[(Supabase Postgres)]
    API --> REDIS[(Redis)]
    API --> SHOPIFY[Shopify Admin API]
    API --> LLM[LLM Provider]
    REDIS --> WORKER[Celery Worker]
    REDIS --> BEAT[Celery Beat]
    WORKER --> DB
    WORKER --> SHOPIFY
    WORKER --> LLM
    BEAT --> REDIS
```

- FastAPI is the main application boundary.
- Postgres stores internal state, logs, drafts, reviews, and approvals.
- Shopify remains the source of truth for commerce data.
- Celery handles long-running sync, generation, and execution work.

## Backend Internal Architecture

```mermaid
graph LR
    ROUTES[API Routes] --> SERVICES[Services]
    SERVICES --> MODULES[Domain Modules]
    MODULES --> REPOS[Repositories]
    MODULES --> INTS[Integrations]
    MODULES --> AGENTS[Agents]
    SERVICES --> TASKS[Task Dispatch]
    TASKS --> REDIS[(Redis)]
    REDIS --> WORKER[Workers]
    WORKER --> MODULES
```

- Routes stay thin.
- Modules hold business rules.
- Workers reuse the same service and module logic instead of duplicating behavior.

## Domain Map

```mermaid
graph TD
    STORES[Stores / Integrations]
    SYNC[Sync]
    CATALOG[Catalog]
    APPROVALS[Approvals]
    SUPPORT[Support]
    POLICIES[Policies]
    FRAUD[Fraud]
    INVENTORY[Inventory]
    ANALYTICS[Analytics]
    WORKFLOWS[Workflow Runs]
    AGENTRUNS[Agent Runs]
    AUDIT[Audit Events]
    NOTIFS[Notifications]

    STORES --> SYNC
    SYNC --> CATALOG
    SYNC --> FRAUD
    SYNC --> INVENTORY
    SYNC --> ANALYTICS
    CATALOG --> APPROVALS
    APPROVALS --> WORKFLOWS
    SUPPORT --> POLICIES
    SUPPORT --> AGENTRUNS
    FRAUD --> WORKFLOWS
    INVENTORY --> WORKFLOWS
    WORKFLOWS --> AUDIT
    WORKFLOWS --> NOTIFS
```

- P0 centers on sync, catalog drafts, approvals, and publish-back.
- P1 adds support, policy retrieval, fraud review, inventory alerts, and analytics.
- P1 and P2 also now use dedicated agent runners for fraud/risk, inventory reorder reasoning, and pricing recommendation flows.

## Runtime Deployment View

```mermaid
graph TD
    subgraph AppRuntime
        API[FastAPI Container]
        WORKER[Celery Worker]
        BEAT[Celery Beat]
        REDIS[(Redis)]
    end

    subgraph DataPlatform
        DB[(Supabase Postgres)]
        AUTH[Supabase Auth]
    end

    subgraph External
        SHOPIFY[Shopify]
        LLM[LLM Provider]
    end

    API --> REDIS
    WORKER --> REDIS
    BEAT --> REDIS
    API --> DB
    WORKER --> DB
    API --> AUTH
    API --> SHOPIFY
    WORKER --> SHOPIFY
    API --> LLM
    WORKER --> LLM
```

- Docker Compose runs the app services.
- Supabase is external in local development.

## Sync And Data Refresh Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Redis
    participant Worker
    participant Shopify

    Client->>API: POST sync-run
    API->>DB: create queued sync_run
    API->>Redis: enqueue sync task
    API-->>Client: 202 Accepted
    Redis->>Worker: deliver task
    Worker->>DB: mark running
    Worker->>Shopify: fetch products, variants, customers, orders
    Worker->>DB: upsert imported records
    Worker->>DB: create fraud and inventory post-processing shells
    Worker->>Redis: enqueue fraud and inventory agent work
    Worker->>DB: mark succeeded or failed
```

- Sync is asynchronous.
- Fraud and inventory logic run after import, not before it.
- Those domains now hand off to dedicated agent tasks after sync shell records are persisted.

## Draft And Approval Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Redis
    participant Worker
    participant LLM
    participant Shopify

    Client->>API: generate draft
    API->>DB: create workflow_run + agent_run
    API->>Redis: enqueue generation
    Redis->>Worker: run agent flow
    Worker->>LLM: generate structured output
    Worker->>DB: save draft
    Client->>API: approve draft
    API->>Redis: enqueue publish execution
    Redis->>Worker: publish approved content
    Worker->>Shopify: product update
    Worker->>DB: mark executed + log audit
```

- AI generation and store execution are separate phases.
- Approval remains the safety boundary for Shopify writes.

## Support And Policy Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Redis
    participant Worker
    participant LLM

    Client->>API: create conversation + inbound message
    API->>DB: persist support state
    Client->>API: generate support draft
    API->>Redis: enqueue support draft task
    Redis->>Worker: run support agent
    Worker->>DB: load conversation, order, customer, policy chunks
    Worker->>LLM: generate reply draft
    Worker->>DB: save draft_outbound message
```

- Support drafts stay internal.
- Policy chunks and order context ground the generated reply.

## Operational Agent Flows

```mermaid
graph TD
    SYNC[Sync completion] --> FRAUDSHELL[Fraud shell records]
    SYNC --> INVSHELL[Inventory alert shells]
    FRAUDSHELL --> FRAUDAGENT[Fraud/Risk Agent task]
    INVSHELL --> INVAGENT[Inventory Agent task]
    PRICEINPUT[Pricing reference input or simulation] --> PRICEAGENT[Pricing Agent task or sync simulation path]
    FRAUDAGENT --> RISKREVIEWS[Risk reviews and order risk fields]
    INVAGENT --> REORDER[Reorder suggestions and supplier drafts]
    PRICEAGENT --> PRICERECS[Price recommendations and optional approvals]
```

- Inventory, fraud/risk, and pricing now follow the same persisted `workflow_run` + `agent_run` model as the earlier product-content and support agents.
- Deterministic validation still runs after the agent output before final business records are updated.
