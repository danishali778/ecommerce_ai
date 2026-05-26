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
| `Inventory Agent` | `P1` direction | support operational inventory reasoning | recommendation support |
| `Fraud/Risk Agent` | `P1` direction | explain risk signals | review context or explanation |
| `Pricing Agent` | `P2` | produce pricing recommendations | simulation or recommendation |

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
- Most flows are controlled generation pipelines, not large autonomous graphs yet.

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
| Operational reasoning | risk explanation, reorder rationale |
