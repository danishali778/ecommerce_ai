-- CommerceOps AI P2 backend-first schema extensions
-- Adds pricing rules and recommendations, user-authored workflow definition fields,
-- and external notification channels, preferences, and deliveries.

alter table commerce_ops.workflows
  add column if not exists store_id uuid null references commerce_ops.stores(id) on delete cascade,
  add column if not exists description text null,
  add column if not exists condition_groups_json jsonb not null default '[]'::jsonb,
  add column if not exists actions_json jsonb not null default '[]'::jsonb,
  add column if not exists version_number integer not null default 1,
  add column if not exists created_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  add column if not exists updated_by_user_id uuid null references commerce_ops.users(id) on delete set null;

create index if not exists workflows_store_trigger_active_idx
  on commerce_ops.workflows (store_id, trigger_type, is_active);

create table if not exists commerce_ops.pricing_rules (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  product_id uuid null references commerce_ops.products(id) on delete cascade,
  variant_id uuid null references commerce_ops.product_variants(id) on delete cascade,
  strategy text not null,
  delta_amount numeric(14, 4) null,
  delta_percentage numeric(8, 4) null,
  markup_percentage numeric(8, 4) null,
  surge_percentage numeric(8, 4) null,
  manual_target_price numeric(14, 4) null,
  cost numeric(14, 4) null,
  margin_floor numeric(14, 4) null,
  price_ceiling numeric(14, 4) null,
  approval_threshold_percent numeric(8, 4) null,
  force_review boolean not null default false,
  is_enabled boolean not null default true,
  version_number integer not null default 1,
  created_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  updated_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists pricing_rules_store_enabled_idx
  on commerce_ops.pricing_rules (store_id, is_enabled, updated_at desc);

create table if not exists commerce_ops.price_reference_inputs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  pricing_rule_id uuid null references commerce_ops.pricing_rules(id) on delete set null,
  product_id uuid null references commerce_ops.products(id) on delete cascade,
  variant_id uuid null references commerce_ops.product_variants(id) on delete cascade,
  source_type text not null default 'manual',
  reference_label text null,
  import_batch_id text null,
  reference_price numeric(14, 4) null,
  cost_override numeric(14, 4) null,
  margin_floor_override numeric(14, 4) null,
  price_ceiling_override numeric(14, 4) null,
  payload_json jsonb not null default '{}'::jsonb,
  created_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists price_reference_inputs_store_source_idx
  on commerce_ops.price_reference_inputs (store_id, source_type, created_at desc);

create table if not exists commerce_ops.price_recommendations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  pricing_rule_id uuid null references commerce_ops.pricing_rules(id) on delete set null,
  reference_input_id uuid null references commerce_ops.price_reference_inputs(id) on delete set null,
  product_id uuid null references commerce_ops.products(id) on delete cascade,
  variant_id uuid null references commerce_ops.product_variants(id) on delete cascade,
  workflow_run_id uuid null references commerce_ops.workflow_runs(id) on delete set null,
  approval_request_id uuid null references commerce_ops.approval_requests(id) on delete set null,
  superseded_by_recommendation_id uuid null references commerce_ops.price_recommendations(id) on delete set null,
  current_price numeric(14, 4) null,
  recommended_price numeric(14, 4) null,
  cost_snapshot numeric(14, 4) null,
  margin_floor_snapshot numeric(14, 4) null,
  price_ceiling_snapshot numeric(14, 4) null,
  reference_price_snapshot numeric(14, 4) null,
  applied_strategy text not null,
  validation_status text not null default 'valid',
  status text not null default 'draft',
  requires_approval boolean not null default false,
  explanation_json jsonb not null default '{}'::jsonb,
  strategy_inputs_json jsonb not null default '{}'::jsonb,
  created_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists price_recommendations_store_status_idx
  on commerce_ops.price_recommendations (store_id, status, created_at desc);

create table if not exists commerce_ops.notification_channels (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  name text not null,
  channel_type text not null,
  status text not null default 'connected',
  is_enabled boolean not null default true,
  metadata_json jsonb not null default '{}'::jsonb,
  secret_reference text null,
  last_test_status text null,
  last_test_error text null,
  last_tested_at timestamptz null,
  created_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  updated_by_user_id uuid null references commerce_ops.users(id) on delete set null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists notification_channels_store_type_idx
  on commerce_ops.notification_channels (store_id, channel_type, is_enabled);

create table if not exists commerce_ops.notification_preferences (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  channel_id uuid not null references commerce_ops.notification_channels(id) on delete cascade,
  event_type text not null,
  is_enabled boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists notification_preferences_channel_event_uidx
  on commerce_ops.notification_preferences (channel_id, event_type);

create table if not exists commerce_ops.notification_deliveries (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid not null references commerce_ops.stores(id) on delete cascade,
  notification_id uuid not null references commerce_ops.notifications(id) on delete cascade,
  channel_id uuid not null references commerce_ops.notification_channels(id) on delete cascade,
  event_type text not null,
  status text not null default 'queued',
  rendered_payload_json jsonb not null default '{}'::jsonb,
  response_payload_json jsonb not null default '{}'::jsonb,
  last_error text null,
  attempt_count integer not null default 0,
  queued_at timestamptz not null default timezone('utc', now()),
  last_attempted_at timestamptz null,
  sent_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists notification_deliveries_store_status_idx
  on commerce_ops.notification_deliveries (store_id, status, created_at desc);

drop trigger if exists pricing_rules_set_updated_at on commerce_ops.pricing_rules;
create trigger pricing_rules_set_updated_at
before update on commerce_ops.pricing_rules
for each row execute function commerce_ops.set_updated_at();

drop trigger if exists price_reference_inputs_set_updated_at on commerce_ops.price_reference_inputs;
create trigger price_reference_inputs_set_updated_at
before update on commerce_ops.price_reference_inputs
for each row execute function commerce_ops.set_updated_at();

drop trigger if exists price_recommendations_set_updated_at on commerce_ops.price_recommendations;
create trigger price_recommendations_set_updated_at
before update on commerce_ops.price_recommendations
for each row execute function commerce_ops.set_updated_at();

drop trigger if exists notification_channels_set_updated_at on commerce_ops.notification_channels;
create trigger notification_channels_set_updated_at
before update on commerce_ops.notification_channels
for each row execute function commerce_ops.set_updated_at();

drop trigger if exists notification_preferences_set_updated_at on commerce_ops.notification_preferences;
create trigger notification_preferences_set_updated_at
before update on commerce_ops.notification_preferences
for each row execute function commerce_ops.set_updated_at();

insert into commerce_ops.workflows (
  organization_id,
  store_id,
  name,
  key,
  description,
  phase_scope,
  trigger_type,
  condition_json,
  action_type,
  condition_groups_json,
  actions_json,
  approval_required,
  is_system_defined,
  is_active,
  version_number
)
values
  (null, null, 'Pricing Recommendation Created', 'pricing_recommendation_created', 'System workflow placeholder for pricing recommendations', 'p2', 'pricing.recommendation.created', '{}'::jsonb, 'log_audit_event', '[]'::jsonb, '[{"type":"log_audit_event","params":{}}]'::jsonb, false, true, true, 1),
  (null, null, 'Workflow Failed', 'workflow_failed', 'System workflow placeholder for workflow failure events', 'p2', 'workflow.failed', '{}'::jsonb, 'log_audit_event', '[]'::jsonb, '[{"type":"log_audit_event","params":{}}]'::jsonb, false, true, true, 1)
on conflict (key) do update
set
  name = excluded.name,
  description = excluded.description,
  phase_scope = excluded.phase_scope,
  trigger_type = excluded.trigger_type,
  condition_json = excluded.condition_json,
  action_type = excluded.action_type,
  condition_groups_json = excluded.condition_groups_json,
  actions_json = excluded.actions_json,
  approval_required = excluded.approval_required,
  is_system_defined = excluded.is_system_defined,
  is_active = excluded.is_active,
  version_number = excluded.version_number,
  updated_at = timezone('utc', now());
