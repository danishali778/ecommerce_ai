# CommerceOps AI - Schema Design

The schema combines imported Shopify records with internal workflow, draft, approval, and review entities.

## Data Model Context

```mermaid
graph TD
    SHOPIFY[Shopify Data] --> IMPORTED[Imported Commerce Tables]
    APP[App Workflows] --> INTERNAL[Internal State Tables]
    AI[Agent Outputs] --> INTERNAL
    INTERNAL --> ANALYTICS[Analytics Reads]
```

- Shopify is the external commerce source.
- Internal tables store workflow and operator state.

## Scope And Identity

```mermaid
erDiagram
    organizations ||--o{ users : has
    organizations ||--o{ stores : has
    users ||--o{ user_roles : assigned
    roles ||--o{ user_roles : grants
    stores ||--o{ integrations : connects
```

- `organization` is the business root.
- `store` scopes imported commerce data and operational workflows.

## Commerce Import Model

```mermaid
erDiagram
    stores ||--o{ products : imports
    products ||--o{ product_variants : has
    stores ||--o{ customers : imports
    customers ||--o{ orders : places
    orders ||--o{ order_items : contains
```

- Products, customers, and orders are synced snapshots.
- These tables feed catalog, support, fraud, inventory, and analytics flows.

## Workflow And Execution Model

```mermaid
erDiagram
    stores ||--o{ sync_runs : tracks
    workflows ||--o{ workflow_runs : executes
    workflow_runs ||--o{ agent_runs : logs
    products ||--o{ product_content_drafts : drafts
    product_content_drafts ||--o{ approval_requests : submitted_for
    approval_requests ||--o{ audit_events : logs
    users ||--o{ notifications : receives
```

- `sync_runs` track import jobs.
- `workflow_runs` and `agent_runs` track async system activity.
- `approval_requests` protect execution-governed actions.

## Support And Policy Model

```mermaid
erDiagram
    stores ||--o{ support_conversations : has
    support_conversations ||--o{ support_messages : contains
    stores ||--o{ policy_documents : owns
    policy_documents ||--o{ policy_document_chunks : chunks
```

- Support messages hold inbound text and draft replies.
- Policy chunks are the retrieval layer for grounded support generation.

## Fraud And Inventory Model

```mermaid
erDiagram
    agent_runs ||--o{ risk_reviews : explains
    agent_runs ||--o{ reorder_suggestions : generates
    orders ||--o{ risk_reviews : reviewed
    product_variants ||--o{ inventory_alerts : triggers
    inventory_alerts ||--o{ reorder_suggestions : creates
    reorder_suggestions ||--o{ supplier_reorder_drafts : drafts
```

- Fraud uses stored order risk plus agent-linked review records.
- Inventory uses alerts, agent-linked suggestions, and supplier drafts as operator artifacts.

## Pricing Recommendation Model

```mermaid
erDiagram
    agent_runs ||--o{ price_recommendations : generates
    price_reference_inputs ||--o{ price_recommendations : informs
    pricing_rules ||--o{ price_recommendations : governs
```

- Pricing recommendations remain business records, but now carry surfaced agent rationale and review metadata.
- `agent_run_id` links operational records back to runtime traces rather than duplicating full runtime state in business tables.

## Full Core ERD

```mermaid
erDiagram
    organizations ||--o{ users : has
    organizations ||--o{ stores : has
    users ||--o{ user_roles : assigned
    roles ||--o{ user_roles : grants
    stores ||--o{ integrations : connects

    stores ||--o{ products : imports
    products ||--o{ product_variants : has
    stores ||--o{ customers : imports
    customers ||--o{ orders : places
    orders ||--o{ order_items : contains

    stores ||--o{ sync_runs : tracks
    workflows ||--o{ workflow_runs : executes
    workflow_runs ||--o{ agent_runs : logs
    products ||--o{ product_content_drafts : drafts
    product_content_drafts ||--o{ approval_requests : submitted_for
    approval_requests ||--o{ audit_events : logs
    users ||--o{ notifications : receives

    stores ||--o{ support_conversations : has
    support_conversations ||--o{ support_messages : contains
    stores ||--o{ policy_documents : owns
    policy_documents ||--o{ policy_document_chunks : chunks

    orders ||--o{ risk_reviews : reviewed
    product_variants ||--o{ inventory_alerts : triggers
    inventory_alerts ||--o{ reorder_suggestions : creates
    reorder_suggestions ||--o{ supplier_reorder_drafts : drafts
```

## Table Families

| Family | Main Tables |
|---|---|
| Scope and access | `organizations`, `users`, `roles`, `user_roles`, `stores`, `integrations` |
| Commerce import | `products`, `product_variants`, `customers`, `orders`, `order_items` |
| Workflow state | `sync_runs`, `workflows`, `workflow_runs`, `agent_runs` |
| Catalog publish flow | `product_content_drafts`, `approval_requests`, `audit_events`, `notifications` |
| P1 support | `support_conversations`, `support_messages`, `policy_documents`, `policy_document_chunks` |
| P1 operations | `risk_reviews`, `inventory_alerts`, `reorder_suggestions`, `supplier_reorder_drafts` |
| P2 pricing operations | `pricing_rules`, `price_reference_inputs`, `price_recommendations` |

## Agent-Linked Business Fields

The operational business tables now surface selected agent-derived fields directly for API and UI use:

- `reorder_suggestions`
  - `agent_run_id`
  - `rationale_summary`
  - `urgency`
  - `confidence_score`
  - `needs_human_review`
  - `review_reason_code`
- `risk_reviews`
  - `agent_run_id`
  - `explanation_json`
  - `explanation_summary`
  - `confidence_score`
  - `needs_human_review`
  - `review_reason_code`
  - `recommended_decision`
- `price_recommendations`
  - `agent_run_id`
  - `explanation_summary`
  - `confidence_score`
  - `needs_human_review`
  - `review_reason_code`
