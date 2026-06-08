# CommerceOps AI - API Design

The API is organized around operator workflows. Some endpoints complete immediately, while generation, sync, and execution endpoints queue background work and return `202 Accepted`.

## API Surface Context

```mermaid
graph TD
    CLIENT[Client / Swagger] --> AUTH[Auth APIs]
    CLIENT --> STORES[Store + Integration APIs]
    CLIENT --> SYNC[Sync APIs]
    CLIENT --> PRODUCTS[Catalog + Draft APIs]
    CLIENT --> APPROVALS[Approval APIs]
    CLIENT --> SUPPORT[Support APIs]
    CLIENT --> POLICIES[Policy APIs]
    CLIENT --> FRAUD[Fraud APIs]
    CLIENT --> INVENTORY[Inventory APIs]
    CLIENT --> ANALYTICS[Analytics APIs]
```

## Request Execution Model

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant DB as Postgres
    participant Q as Redis
    participant W as Worker

    C->>API: HTTP request
    API->>DB: validate auth, scope, state
    alt direct request
        API->>DB: read/write resource
        API-->>C: 200 / 201
    else async request
        API->>Q: enqueue task
        API-->>C: 202 Accepted
        Q->>W: execute task
        W->>DB: persist final result
    end
```

- Reads and small writes are synchronous.
- Sync, AI generation, and publish execution are asynchronous.

## Route Groups

| Group | Main Purpose | Typical Mode |
|---|---|---|
| `auth` | login, logout, current user, session refresh | sync |
| `stores` | store records and Shopify install flow | sync |
| `sync-runs` | start sync, retry sync, inspect sync history | async trigger + sync reads |
| `products` | product reads and content draft workflows | mixed |
| `approvals` | review and execute publish-governed actions | mixed |
| `support` | conversations, messages, reply drafts | mixed |
| `policies` | policy CRUD and retrieval source material | mixed |
| `fraud` | order risk score and review queue | sync-triggered agent writes + sync reads |
| `inventory` | alerts, reorder suggestions, supplier drafts | sync-triggered agent writes + sync reads |
| `pricing` | pricing rules, simulations, and recommendations | mixed |
| `analytics` | overview and automation metrics | sync |

## Auth API Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Supabase
    participant DB

    Client->>API: login / refresh / me
    API->>Supabase: authenticate or verify session
    API->>DB: load app user + roles
    API-->>Client: token context + permissions
```

- Auth is backed by Supabase Auth.
- App roles and store scope come from the app database.

## Store And Shopify Connect Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Shopify

    Client->>API: create store
    API->>DB: persist store record
    Client->>API: request install URL
    API->>DB: persist oauth state
    API-->>Client: install URL
    Client->>Shopify: install app
    Shopify->>API: OAuth callback
    API->>DB: persist integration status
```

- Store creation and Shopify connection are separate steps.
- The callback finishes the connection state in the backend.

## Sync API Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Redis
    participant Worker

    Client->>API: POST /sync-runs
    API->>DB: create sync_run queued
    API->>Redis: enqueue sync task
    API-->>Client: 202 + sync_run_id
    Redis->>Worker: execute sync
    Worker->>DB: update sync status + counts
    Client->>API: GET sync status
    API-->>Client: current sync_run state
```

- Sync APIs are command + polling style.

## Product Draft API Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Redis
    participant Worker
    participant LLM

    Client->>API: generate content draft
    API->>DB: create workflow_run + agent_run
    API->>Redis: enqueue generation
    API-->>Client: 202 + run ids
    Redis->>Worker: generate draft
    Worker->>LLM: structured generation
    Worker->>DB: save product_content_draft
    Client->>API: fetch draft
```

- Draft generation is asynchronous.
- Draft review and edit happen before approval submission.

## Approval And Publish API Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Redis
    participant Worker
    participant Shopify

    Client->>API: submit approval / approve
    API->>DB: validate approval state
    API->>Redis: enqueue execution
    API-->>Client: approval state
    Redis->>Worker: execute publish
    Worker->>Shopify: update product
    Worker->>DB: mark executed or failed
```

- Approvals protect risky store writes.
- Execution runs separately from human review.

## Support And Policy API Flow

```mermaid
graph TD
    CONV[Support Conversations API] --> MSG[Support Messages API]
    MSG --> DRAFT[Reply Draft Generation API]
    POL[Policies API] --> DRAFT
    DRAFT --> RUNS[Workflow Run + Agent Run]
    DRAFT --> OUT[Draft Outbound Message]
```

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Redis
    participant Worker
    participant LLM

    Client->>API: create policy / conversation / message
    API->>DB: persist inputs
    Client->>API: generate reply draft
    API->>Redis: enqueue support task
    Redis->>Worker: load policy chunks + order/customer context
    Worker->>LLM: generate support draft
    Worker->>DB: save cited draft message
```

- Policies act as retrieval source documents.
- Support drafts stay internal and can be flagged for review.

## Fraud API Flow

```mermaid
sequenceDiagram
    participant Sync as Sync Worker
    participant Fraud as Fraud Module
    participant Agent as Fraud/Risk Agent
    participant DB as Postgres
    participant Client
    participant API

    Sync->>Fraud: create agent run for imported order
    Fraud->>Agent: enqueue fraud task
    Agent->>DB: update risk_score + risk_status
    Agent->>DB: create or update risk_review if review is required
    Client->>API: GET order risk score / risk reviews
    API->>DB: read fraud state
    API-->>Client: risk data
```

- Fraud assessment is triggered by sync, not by a standalone generation endpoint.
- Review APIs expose stored score, explanation, review metadata, and `agent_run_id`.

## Inventory API Flow

```mermaid
sequenceDiagram
    participant Sync as Sync Worker
    participant Inv as Inventory Module
    participant Agent as Inventory Agent
    participant DB as Postgres
    participant Client
    participant API

    Sync->>Inv: evaluate imported variants
    Inv->>DB: create or update inventory alerts
    Inv->>Agent: enqueue inventory task for below-threshold alerts
    Agent->>DB: create or update reorder suggestions
    Agent->>DB: create optional supplier draft
    Client->>API: list alerts / suggestions / drafts
    API->>DB: read inventory state
    API-->>Client: inventory intelligence
```

- Inventory APIs mainly expose worker-produced operational state.
- Suggestion responses include surfaced rationale, review metadata, and `agent_run_id`.

## Pricing API Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Redis
    participant Worker
    participant Agent as Pricing Agent
    participant LLM

    Client->>API: create reference input or CSV import
    API->>DB: persist reference input + agent run shell
    API->>Redis: enqueue pricing task
    Redis->>Worker: execute pricing task
    Worker->>Agent: run pricing recommendation flow
    Agent->>LLM: generate structured recommendation
    Agent->>DB: save price_recommendation and optional approval link
    Client->>API: fetch recommendation or simulate pricing
```

- Pricing simulation and recommendation responses are agent-backed.
- Business guardrails still block below-floor, above-ceiling, or unsafe recommendation outputs.

## Analytics API Flow

```mermaid
graph LR
    API[Analytics APIs] --> PRODUCTS[Catalog Data]
    API --> ORDERS[Order Data]
    API --> SUPPORT[Support Data]
    API --> FRAUD[Fraud Data]
    API --> INV[Inventory Data]
    API --> RUNS[Workflow + Agent + Approval Data]
```

- Analytics are read-only aggregate endpoints.
- They summarize live application state rather than triggering new workflows.
