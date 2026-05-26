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
    orders ||--o{ risk_reviews : reviewed
    product_variants ||--o{ inventory_alerts : triggers
    inventory_alerts ||--o{ reorder_suggestions : creates
    reorder_suggestions ||--o{ supplier_reorder_drafts : drafts
```

- Fraud uses stored order risk plus optional review records.
- Inventory uses alerts, suggestions, and supplier drafts as operator artifacts.

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
