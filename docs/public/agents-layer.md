# CommerceOps AI - Agents Layer

The agents layer is the AI execution layer inside the backend. It produces drafts, recommendations, and explanations, then hands results back to the normal workflow and review system.

## Agent Layer Context

```mermaid
graph TD
    ROUTE[API Route or Task] --> SERVICE[Service]
    SERVICE --> MODULE[Module]
    MODULE --> AGENT[Agent Runner]
    AGENT --> LLM[LLM Provider]
    AGENT --> RESULT[Structured Result]
    RESULT --> DB[(Drafts / Reviews / Logs)]
```

- Agents sit inside backend workflows, not outside them.
- They produce structured outputs rather than directly mutating Shopify.

## Current And Planned Agents

```mermaid
graph LR
    P0[Product Content Agent]
    P1A[Support Agent]
    P1B[Inventory Agent]
    P1C[Fraud/Risk Agent]
    P2[Pricing Agent]
```

| Agent | Phase | Purpose | Main Output |
|---|---|---|---|
| `Product Content Agent` | `P0` | generate product content drafts | draft title, description, tags, SEO |
| `Support Agent` | `P1` | generate policy-grounded support drafts | reply draft, confidence, review flags |
| `Inventory Agent` | `P1` implemented | reason about low-stock and reorder needs | reorder suggestion, draft supplier copy, review flags |
| `Fraud/Risk Agent` | `P1` implemented | assess order risk and produce review-ready evidence | normalized score, review context, recommended decision |
| `Pricing Agent` | `P2` implemented | produce pricing recommendations and simulations | recommendation or simulation with rationale and review metadata |

## Agent Execution Pattern

```mermaid
sequenceDiagram
    participant API
    participant DB
    participant Agent
    participant LLM

    API->>DB: load authorized context
    API->>Agent: invoke runner
    Agent->>LLM: generate structured output
    LLM-->>Agent: model result
    Agent->>Agent: validate output schema
    Agent->>DB: persist result and run logs
```

- The API or worker prepares the context first.
- The agent returns typed output that can be stored safely.

## LangGraph Pattern In This Repo

```mermaid
graph LR
    START[Input state] --> GENERATE[Generate node]
    GENERATE --> VALIDATE[Validation step]
    VALIDATE --> END[Persisted result]
```

- Current LangGraph usage is intentionally lightweight.
- Most flows are controlled generation pipelines with structured outputs, persisted `agent_runs`, and deterministic post-validation.

## Product Content Agent Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Worker
    participant Agent
    participant LLM
    participant DB

    Client->>API: generate product draft
    API->>DB: create workflow_run + agent_run
    API->>Worker: enqueue task
    Worker->>Agent: run product content flow
    Agent->>LLM: generate content
    Agent->>DB: save product_content_draft
```

- This is the current P0 production path.

## Support Agent Flow

```mermaid
sequenceDiagram
    participant API
    participant Worker
    participant DB
    participant Agent
    participant LLM

    API->>Worker: enqueue support draft task
    Worker->>DB: load conversation + order + customer + policy chunks
    Worker->>Agent: run support flow
    Agent->>LLM: generate reply draft
    Agent->>DB: save support draft message
```

- Support drafts are grounded with policy and commerce context.
- Low-confidence results are flagged for review.

## Inventory Agent Flow

```mermaid
sequenceDiagram
    participant Sync as Sync Worker
    participant DB
    participant Agent
    participant LLM

    Sync->>DB: create inventory alert shell
    Sync->>DB: create workflow_run + agent_run
    Sync->>Agent: enqueue inventory agent task
    Agent->>DB: load variant, product, and alert context
    Agent->>LLM: generate reorder suggestion
    Agent->>DB: save reorder_suggestion and optional supplier draft
```

- The agent is the primary reorder reasoner.
- Quantity validation and draft-only safety remain deterministic after output parsing.

## Fraud/Risk Agent Flow

```mermaid
sequenceDiagram
    participant Sync as Sync Worker
    participant DB
    participant Agent
    participant LLM

    Sync->>DB: create workflow_run + agent_run for imported order
    Sync->>Agent: enqueue fraud/risk task
    Agent->>DB: load order, customer, and prior review context
    Agent->>LLM: generate score, evidence, and review recommendation
    Agent->>DB: update order risk fields and create/update risk_review
```

- The agent is the primary risk reasoner.
- Fraud decisions still remain manual and internal-only.

## Pricing Agent Flow

```mermaid
sequenceDiagram
    participant API
    participant DB
    participant Agent
    participant LLM

    API->>DB: create price_reference_input
    API->>DB: create workflow_run + agent_run
    API->>Agent: enqueue pricing task
    Agent->>DB: load pricing rule, reference input, and economics context
    Agent->>LLM: generate recommendation or simulation output
    Agent->>DB: save price_recommendation and optional approval linkage
```

- The pricing agent is the primary reasoning layer for both persisted recommendations and simulation.
- Margin floor, ceiling, and approval-threshold enforcement remain deterministic after the agent output.

## Agent Safety Boundaries

```mermaid
graph TD
    AGENT[Agent Output] --> REVIEW[Review / Approval Layer]
    REVIEW --> EXEC[Execution Path]
    EXEC --> SHOPIFY[Shopify Write]
```

- Agents do not publish directly to Shopify.
- Risky actions stay behind review or approval gates.
- Workflow and agent runs provide traceability for every important execution.
- Inventory supplier communication remains draft-only.
- Fraud remains review-only and does not mutate store state.
- Pricing recommendations never publish directly to Shopify.

## Inputs And Outputs

| Input Type | Examples |
|---|---|
| Commerce context | products, variants, orders, customers |
| Policy context | policy documents and chunks |
| Operator context | requested tone, target fields, instructions |
| Workflow context | store id, user id, conversation id, product id |

| Output Type | Examples |
|---|---|
| Drafts | product content draft, support reply draft |
| Review signals | confidence score, needs review, rationale |
| Operational reasoning | risk explanation, reorder rationale, pricing recommendation rationale |
