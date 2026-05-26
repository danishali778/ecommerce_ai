-- CommerceOps AI P1 operator schema extensions
-- Adds support workspace, policy retrieval, fraud reviews, inventory alerts, reorder drafts, and analytics source tables.

alter table commerce_ops.agent_runs
  drop constraint if exists agent_runs_agent_type_check;

alter table commerce_ops.agent_runs
  add constraint agent_runs_agent_type_check
  check (agent_type in ('product_content', 'support', 'support_reply', 'inventory', 'fraud_risk', 'pricing', 'analytics'));

create table if not exists commerce_ops.support_conversations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  customer_id uuid null references commerce_ops.customers(id) on delete set null,
  order_id uuid null references commerce_ops.orders(id) on delete set null,
  external_ticket_id text null,
  channel text not null default 'internal_console',
  status text not null default 'open',
  assigned_user_id uuid null references commerce_ops.users(id) on delete set null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists support_conversations_store_updated_idx
  on commerce_ops.support_conversations (store_id, updated_at);

create table if not exists commerce_ops.support_messages (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  conversation_id uuid not null references commerce_ops.support_conversations(id) on delete cascade,
  direction text not null,
  body text not null,
  generated_by_ai boolean not null default false,
  confidence_score numeric(5, 4) null,
  needs_human_review boolean not null default false,
  review_reason_code text null,
  status text not null default 'logged',
  cited_policy_chunks_json jsonb not null default '[]'::jsonb,
  cited_order_facts_summary text null,
  created_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists support_messages_conversation_created_idx
  on commerce_ops.support_messages (conversation_id, created_at);

create table if not exists commerce_ops.policy_documents (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  document_type text not null,
  source_type text not null default 'manual',
  title text not null,
  content text not null,
  version text null,
  is_active boolean not null default true,
  embedding_status text not null default 'pending',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists policy_documents_store_document_type_uidx
  on commerce_ops.policy_documents (store_id, document_type);

create table if not exists commerce_ops.policy_document_chunks (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  policy_document_id uuid not null references commerce_ops.policy_documents(id) on delete cascade,
  document_type text not null,
  chunk_index integer not null,
  content text not null,
  embedding_json jsonb null,
  token_count integer null,
  created_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists policy_document_chunks_doc_index_uidx
  on commerce_ops.policy_document_chunks (policy_document_id, chunk_index);

create index if not exists policy_document_chunks_store_type_idx
  on commerce_ops.policy_document_chunks (store_id, document_type);

create table if not exists commerce_ops.inventory_alerts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  product_id uuid not null references commerce_ops.products(id) on delete cascade,
  variant_id uuid not null references commerce_ops.product_variants(id) on delete cascade,
  threshold_value integer not null,
  current_quantity integer not null,
  status text not null default 'open',
  resolved_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists inventory_alerts_variant_status_uidx
  on commerce_ops.inventory_alerts (store_id, variant_id, status);

create index if not exists inventory_alerts_store_status_created_idx
  on commerce_ops.inventory_alerts (store_id, status, created_at);

create table if not exists commerce_ops.reorder_suggestions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  inventory_alert_id uuid not null references commerce_ops.inventory_alerts(id) on delete cascade,
  product_id uuid not null references commerce_ops.products(id) on delete cascade,
  variant_id uuid null references commerce_ops.product_variants(id) on delete set null,
  recommended_quantity integer not null,
  current_quantity integer not null,
  threshold_value integer not null,
  rationale_json jsonb not null default '{}'::jsonb,
  status text not null default 'open',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists reorder_suggestions_alert_status_uidx
  on commerce_ops.reorder_suggestions (inventory_alert_id, status);

create index if not exists reorder_suggestions_store_status_created_idx
  on commerce_ops.reorder_suggestions (store_id, status, created_at);

create table if not exists commerce_ops.supplier_reorder_drafts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  reorder_suggestion_id uuid not null references commerce_ops.reorder_suggestions(id) on delete cascade,
  vendor_name text not null,
  recipient_email text null,
  subject text not null,
  body text not null,
  status text not null default 'draft',
  created_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists supplier_reorder_drafts_suggestion_uidx
  on commerce_ops.supplier_reorder_drafts (reorder_suggestion_id);

create table if not exists commerce_ops.risk_reviews (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  order_id uuid not null references commerce_ops.orders(id) on delete cascade,
  risk_score integer not null,
  risk_status text not null default 'pending_review',
  reason_codes_json jsonb not null default '[]'::jsonb,
  decision text null,
  decision_notes text null,
  reviewed_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  reviewed_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists risk_reviews_order_status_uidx
  on commerce_ops.risk_reviews (order_id, risk_status);

create index if not exists risk_reviews_store_status_created_idx
  on commerce_ops.risk_reviews (store_id, risk_status, created_at);

drop trigger if exists support_conversations_set_updated_at on commerce_ops.support_conversations;
create trigger support_conversations_set_updated_at
before update on commerce_ops.support_conversations
for each row execute function commerce_ops.set_updated_at();

drop trigger if exists support_messages_set_updated_at on commerce_ops.support_messages;
create trigger support_messages_set_updated_at
before update on commerce_ops.support_messages
for each row execute function commerce_ops.set_updated_at();

drop trigger if exists policy_documents_set_updated_at on commerce_ops.policy_documents;
create trigger policy_documents_set_updated_at
before update on commerce_ops.policy_documents
for each row execute function commerce_ops.set_updated_at();

drop trigger if exists inventory_alerts_set_updated_at on commerce_ops.inventory_alerts;
create trigger inventory_alerts_set_updated_at
before update on commerce_ops.inventory_alerts
for each row execute function commerce_ops.set_updated_at();

drop trigger if exists reorder_suggestions_set_updated_at on commerce_ops.reorder_suggestions;
create trigger reorder_suggestions_set_updated_at
before update on commerce_ops.reorder_suggestions
for each row execute function commerce_ops.set_updated_at();

drop trigger if exists supplier_reorder_drafts_set_updated_at on commerce_ops.supplier_reorder_drafts;
create trigger supplier_reorder_drafts_set_updated_at
before update on commerce_ops.supplier_reorder_drafts
for each row execute function commerce_ops.set_updated_at();

drop trigger if exists risk_reviews_set_updated_at on commerce_ops.risk_reviews;
create trigger risk_reviews_set_updated_at
before update on commerce_ops.risk_reviews
for each row execute function commerce_ops.set_updated_at();

insert into commerce_ops.workflows (
  name,
  key,
  phase_scope,
  trigger_type,
  condition_json,
  action_type,
  approval_required,
  is_system_defined,
  is_active
)
values
  ('Support Reply Draft Generated', 'support_reply_draft_generated', 'p1', 'support_reply_draft_generated', '{}'::jsonb, 'support_draft_saved_and_logged', false, true, true),
  ('High Risk Review Created', 'high_risk_review_created', 'p1', 'high_risk_review_created', '{}'::jsonb, 'risk_review_logged', false, true, true),
  ('Low Stock Alert Created', 'low_stock_alert_created', 'p1', 'low_stock_alert_created', '{}'::jsonb, 'inventory_alert_logged', false, true, true)
on conflict (key) do update
set
  name = excluded.name,
  phase_scope = excluded.phase_scope,
  trigger_type = excluded.trigger_type,
  condition_json = excluded.condition_json,
  action_type = excluded.action_type,
  approval_required = excluded.approval_required,
  is_system_defined = excluded.is_system_defined,
  is_active = excluded.is_active,
  updated_at = timezone('utc', now());
