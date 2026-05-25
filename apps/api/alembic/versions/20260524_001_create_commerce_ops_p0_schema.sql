-- CommerceOps AI P0 core schema
-- NOTE:
-- - Uses a dedicated backend-owned schema to avoid collisions with existing public tables.
-- - Covers P0 core tables only.

create schema if not exists commerce_ops;

create or replace function commerce_ops.set_updated_at()
returns trigger
language plpgsql
set search_path = commerce_ops, pg_temp
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists commerce_ops.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(trim(name)) > 0),
  slug text not null check (char_length(trim(slug)) > 0),
  owner_user_id uuid null,
  status text not null default 'active'
    check (status in ('active', 'suspended', 'archived')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists organizations_slug_uidx
  on commerce_ops.organizations (slug);

create table if not exists commerce_ops.roles (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(trim(name)) > 0),
  description text not null default '',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists roles_name_uidx
  on commerce_ops.roles (name);

create table if not exists commerce_ops.users (
  id uuid primary key references auth.users(id) on delete cascade,
  organization_id uuid null references commerce_ops.organizations(id) on delete set null,
  email text not null check (char_length(trim(email)) > 0),
  full_name text not null default '',
  status text not null default 'active'
    check (status in ('invited', 'active', 'suspended', 'disabled')),
  last_login_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists users_email_lower_uidx
  on commerce_ops.users (lower(email));

create index if not exists users_org_status_idx
  on commerce_ops.users (organization_id, status);

create table if not exists commerce_ops.user_roles (
  user_id uuid not null references commerce_ops.users(id) on delete cascade,
  role_id uuid not null references commerce_ops.roles(id) on delete cascade,
  assigned_at timestamptz not null default timezone('utc', now()),
  assigned_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  primary key (user_id, role_id)
);

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'organizations_owner_user_id_fkey'
      and conrelid = 'commerce_ops.organizations'::regclass
  ) then
    alter table commerce_ops.organizations
      add constraint organizations_owner_user_id_fkey
      foreign key (owner_user_id)
      references commerce_ops.users(id)
      on delete set null;
  end if;
end $$;

create table if not exists commerce_ops.stores (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  platform text not null default 'shopify'
    check (platform in ('shopify', 'woocommerce')),
  name text not null check (char_length(trim(name)) > 0),
  domain text not null check (char_length(trim(domain)) > 0),
  external_store_id text null,
  currency text null,
  timezone text null,
  connection_status text not null default 'pending'
    check (connection_status in ('pending', 'connected', 'disconnected', 'error')),
  last_successful_sync_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists stores_org_domain_uidx
  on commerce_ops.stores (organization_id, domain);

create unique index if not exists stores_org_platform_external_uidx
  on commerce_ops.stores (organization_id, platform, external_store_id)
  where external_store_id is not null;

create index if not exists stores_org_connection_idx
  on commerce_ops.stores (organization_id, connection_status);

create table if not exists commerce_ops.integrations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  provider text not null check (char_length(trim(provider)) > 0),
  provider_account_id text null,
  secret_reference text null,
  scopes text[] not null default '{}'::text[],
  status text not null default 'pending'
    check (status in ('pending', 'connected', 'disconnected', 'error')),
  last_successful_sync_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists integrations_store_provider_uidx
  on commerce_ops.integrations (store_id, provider);

create table if not exists commerce_ops.sync_runs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  integration_id uuid not null references commerce_ops.integrations(id) on delete cascade,
  mode text not null
    check (mode in ('manual_full', 'scheduled_full', 'retry_full', 'demo_seed', 'csv_fallback')),
  status text not null default 'queued'
    check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
  triggered_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  records_imported integer not null default 0,
  records_failed integer not null default 0,
  entity_counts_json jsonb not null default '{}'::jsonb,
  error_summary text null,
  error_details_json jsonb null default '{}'::jsonb,
  retry_of_sync_run_id uuid null references commerce_ops.sync_runs(id) on delete set null,
  started_at timestamptz null,
  completed_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists sync_runs_store_created_idx
  on commerce_ops.sync_runs (store_id, created_at desc);

create unique index if not exists sync_runs_single_active_per_store_uidx
  on commerce_ops.sync_runs (store_id)
  where status in ('queued', 'running');

create table if not exists commerce_ops.products (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  external_product_id text not null,
  handle text not null,
  title text not null,
  description text null,
  vendor text null,
  category text null,
  tags text[] not null default '{}'::text[],
  seo_title text null,
  seo_description text null,
  status text not null default 'active',
  is_archived boolean not null default false,
  archived_at timestamptz null,
  last_sync_run_id uuid null references commerce_ops.sync_runs(id) on delete set null,
  last_synced_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists products_store_external_uidx
  on commerce_ops.products (store_id, external_product_id);

create index if not exists products_store_updated_idx
  on commerce_ops.products (store_id, updated_at desc);

create index if not exists products_tags_gin_idx
  on commerce_ops.products using gin (tags);

create table if not exists commerce_ops.product_variants (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  product_id uuid not null references commerce_ops.products(id) on delete cascade,
  external_variant_id text not null,
  sku text null,
  title text not null default '',
  price numeric(14,4) not null default 0,
  cost numeric(14,4) null,
  inventory_quantity integer not null default 0,
  margin_floor numeric(14,4) null,
  price_ceiling numeric(14,4) null,
  compare_at_price numeric(14,4) null,
  last_sync_run_id uuid null references commerce_ops.sync_runs(id) on delete set null,
  last_synced_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists product_variants_store_external_uidx
  on commerce_ops.product_variants (store_id, external_variant_id);

create unique index if not exists product_variants_store_sku_uidx
  on commerce_ops.product_variants (store_id, sku)
  where sku is not null;

create index if not exists product_variants_store_sku_idx
  on commerce_ops.product_variants (store_id, sku);

create table if not exists commerce_ops.customers (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  external_customer_id text not null,
  email text null,
  first_name text null,
  last_name text null,
  phone text null,
  total_orders integer not null default 0,
  total_spend numeric(14,4) not null default 0,
  total_refunds numeric(14,4) not null default 0,
  last_sync_run_id uuid null references commerce_ops.sync_runs(id) on delete set null,
  last_synced_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists customers_store_external_uidx
  on commerce_ops.customers (store_id, external_customer_id);

create index if not exists customers_store_email_idx
  on commerce_ops.customers (store_id, lower(email));

create table if not exists commerce_ops.orders (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  external_order_id text not null,
  customer_id uuid null references commerce_ops.customers(id) on delete set null,
  status text not null,
  payment_status text null,
  fulfillment_status text null,
  billing_country text null,
  shipping_country text null,
  billing_postal_code text null,
  shipping_postal_code text null,
  payment_attempt_count integer not null default 0,
  subtotal numeric(14,4) not null default 0,
  total numeric(14,4) not null default 0,
  currency text null,
  risk_score integer null,
  risk_status text null,
  last_sync_run_id uuid null references commerce_ops.sync_runs(id) on delete set null,
  last_synced_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists orders_store_external_uidx
  on commerce_ops.orders (store_id, external_order_id);

create index if not exists orders_store_created_idx
  on commerce_ops.orders (store_id, created_at desc);

create index if not exists orders_store_status_idx
  on commerce_ops.orders (store_id, payment_status, fulfillment_status);

create table if not exists commerce_ops.order_items (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  order_id uuid not null references commerce_ops.orders(id) on delete cascade,
  product_id uuid null references commerce_ops.products(id) on delete set null,
  variant_id uuid null references commerce_ops.product_variants(id) on delete set null,
  external_line_item_id text null,
  sku text null,
  title text not null,
  quantity integer not null,
  unit_price numeric(14,4) not null default 0,
  total_price numeric(14,4) not null default 0,
  created_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists order_items_order_external_uidx
  on commerce_ops.order_items (order_id, external_line_item_id)
  where external_line_item_id is not null;

create table if not exists commerce_ops.workflows (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid null references commerce_ops.organizations(id) on delete set null,
  name text not null,
  key text not null,
  phase_scope text not null
    check (phase_scope in ('p0', 'p1', 'p2')),
  trigger_type text not null,
  condition_json jsonb not null default '{}'::jsonb,
  action_type text not null,
  approval_required boolean not null default false,
  is_system_defined boolean not null default true,
  is_active boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists workflows_key_uidx
  on commerce_ops.workflows (key);

create table if not exists commerce_ops.workflow_runs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  workflow_id uuid not null references commerce_ops.workflows(id) on delete cascade,
  trigger_type text not null,
  trigger_entity_type text not null,
  trigger_entity_id uuid null,
  status text not null default 'queued'
    check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
  input_payload jsonb not null default '{}'::jsonb,
  output_payload jsonb not null default '{}'::jsonb,
  error_message text null,
  retry_count integer not null default 0,
  started_at timestamptz null,
  completed_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists workflow_runs_store_created_idx
  on commerce_ops.workflow_runs (store_id, created_at desc);

create table if not exists commerce_ops.product_content_drafts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  product_id uuid not null references commerce_ops.products(id) on delete cascade,
  source_snapshot_json jsonb not null default '{}'::jsonb,
  generated_title text null,
  generated_description text null,
  generated_tags text[] not null default '{}'::text[],
  generated_seo_title text null,
  generated_seo_description text null,
  generation_prompt_version text not null,
  model_name text not null,
  status text not null default 'draft'
    check (status in ('draft', 'submitted_for_approval', 'approved', 'rejected', 'published', 'publish_failed', 'superseded')),
  submitted_approval_request_id uuid null,
  published_at timestamptz null,
  created_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists commerce_ops.agent_runs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  agent_type text not null
    check (agent_type in ('product_content', 'support', 'inventory', 'fraud_risk', 'pricing', 'analytics')),
  user_id uuid null references commerce_ops.users(id) on delete set null,
  workflow_run_id uuid null references commerce_ops.workflow_runs(id) on delete set null,
  input_summary text null,
  retrieved_context_summary text null,
  output_summary text null,
  tool_calls_json jsonb not null default '[]'::jsonb,
  model_name text not null,
  latency_ms integer null,
  token_usage_input integer null,
  token_usage_output integer null,
  status text not null default 'queued'
    check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
  error_message text null,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists agent_runs_store_created_idx
  on commerce_ops.agent_runs (store_id, created_at desc);

create table if not exists commerce_ops.approval_requests (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  action_type text not null
    check (action_type in ('product_content_publish', 'support_reply_send', 'supplier_reorder_send', 'fraud_review_decision', 'pricing_recommendation_approval')),
  entity_type text not null,
  entity_id uuid not null,
  workflow_run_id uuid null references commerce_ops.workflow_runs(id) on delete set null,
  agent_run_id uuid null references commerce_ops.agent_runs(id) on delete set null,
  proposed_action_json jsonb not null default '{}'::jsonb,
  source_snapshot_hash text not null,
  source_snapshot_created_at timestamptz not null,
  reasoning text not null,
  status text not null default 'pending'
    check (status in ('pending', 'approved', 'rejected', 'expired', 'cancelled', 'executed', 'execution_failed')),
  review_notes text null,
  expires_at timestamptz not null default (timezone('utc', now()) + interval '7 days'),
  execution_status text null
    check (
      execution_status is null
      or execution_status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')
    ),
  execution_error text null,
  idempotency_key text not null,
  requested_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  reviewed_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  reviewed_at timestamptz null,
  last_execution_attempt_at timestamptz null,
  retry_count integer not null default 0,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists approval_requests_org_action_idempotency_uidx
  on commerce_ops.approval_requests (organization_id, action_type, idempotency_key);

create unique index if not exists approval_requests_pending_entity_action_uidx
  on commerce_ops.approval_requests (entity_type, entity_id, action_type)
  where status = 'pending';

create index if not exists approval_requests_store_status_created_idx
  on commerce_ops.approval_requests (store_id, status, created_at desc);

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'product_content_drafts_submitted_approval_request_id_fkey'
      and conrelid = 'commerce_ops.product_content_drafts'::regclass
  ) then
    alter table commerce_ops.product_content_drafts
      add constraint product_content_drafts_submitted_approval_request_id_fkey
      foreign key (submitted_approval_request_id)
      references commerce_ops.approval_requests(id)
      on delete set null;
  end if;
end $$;

create table if not exists commerce_ops.audit_events (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid null references commerce_ops.stores(id) on delete set null,
  user_id uuid null references commerce_ops.users(id) on delete set null,
  entity_type text not null,
  entity_id uuid null,
  action_type text not null,
  source_type text not null,
  outcome text not null,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists audit_events_store_created_idx
  on commerce_ops.audit_events (store_id, created_at desc);

create table if not exists commerce_ops.notifications (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid null references commerce_ops.stores(id) on delete set null,
  user_id uuid not null references commerce_ops.users(id) on delete cascade,
  type text not null,
  channel text not null default 'in_app'
    check (channel in ('in_app', 'email', 'slack', 'webhook')),
  title text not null,
  body text not null,
  payload_json jsonb not null default '{}'::jsonb,
  status text not null default 'unread'
    check (status in ('unread', 'read', 'archived')),
  read_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists notifications_user_status_created_idx
  on commerce_ops.notifications (user_id, status, created_at desc);

create or replace trigger organizations_set_updated_at
before update on commerce_ops.organizations
for each row execute function commerce_ops.set_updated_at();

create or replace trigger roles_set_updated_at
before update on commerce_ops.roles
for each row execute function commerce_ops.set_updated_at();

create or replace trigger users_set_updated_at
before update on commerce_ops.users
for each row execute function commerce_ops.set_updated_at();

create or replace trigger stores_set_updated_at
before update on commerce_ops.stores
for each row execute function commerce_ops.set_updated_at();

create or replace trigger integrations_set_updated_at
before update on commerce_ops.integrations
for each row execute function commerce_ops.set_updated_at();

create or replace trigger products_set_updated_at
before update on commerce_ops.products
for each row execute function commerce_ops.set_updated_at();

create or replace trigger product_variants_set_updated_at
before update on commerce_ops.product_variants
for each row execute function commerce_ops.set_updated_at();

create or replace trigger customers_set_updated_at
before update on commerce_ops.customers
for each row execute function commerce_ops.set_updated_at();

create or replace trigger orders_set_updated_at
before update on commerce_ops.orders
for each row execute function commerce_ops.set_updated_at();

create or replace trigger workflows_set_updated_at
before update on commerce_ops.workflows
for each row execute function commerce_ops.set_updated_at();

create or replace trigger product_content_drafts_set_updated_at
before update on commerce_ops.product_content_drafts
for each row execute function commerce_ops.set_updated_at();

create or replace trigger approval_requests_set_updated_at
before update on commerce_ops.approval_requests
for each row execute function commerce_ops.set_updated_at();

insert into commerce_ops.roles (name, description)
values
  ('Owner', 'Business owner with broad operational visibility and approval authority'),
  ('Admin', 'Administrative user with access to users, integrations, settings, approvals, and logs'),
  ('Manager', 'Operational manager for products, orders, inventory, pricing, and workflows'),
  ('Support Agent', 'Internal support user for support workflows and customer-related operations'),
  ('Marketing User', 'User focused on product content drafts and related approvals')
on conflict (name) do update
set description = excluded.description;

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
  ('Store Sync Completed', 'store_sync_completed', 'p0', 'sync_completed', '{}'::jsonb, 'sync_log_and_audit', false, true, true),
  ('Store Sync Failed', 'store_sync_failed', 'p0', 'sync_failed', '{}'::jsonb, 'sync_failure_alert', false, true, true),
  ('Product Content Generated', 'product_content_generated', 'p0', 'product_content_generated', '{}'::jsonb, 'draft_saved_and_logged', false, true, true),
  ('Product Content Publish', 'product_content_publish', 'p0', 'approval_approved', '{}'::jsonb, 'publish_product_content', true, true, true),
  ('Approval Decision Logged', 'approval_decision_logged', 'p0', 'approval_decided', '{}'::jsonb, 'approval_audit_log', false, true, true),
  ('Agent Execution Logged', 'agent_execution_logged', 'p0', 'agent_completed', '{}'::jsonb, 'agent_run_log', false, true, true)
on conflict (key) do update
set
  name = excluded.name,
  phase_scope = excluded.phase_scope,
  trigger_type = excluded.trigger_type,
  condition_json = excluded.condition_json,
  action_type = excluded.action_type,
  approval_required = excluded.approval_required,
  is_system_defined = excluded.is_system_defined,
  is_active = excluded.is_active;
