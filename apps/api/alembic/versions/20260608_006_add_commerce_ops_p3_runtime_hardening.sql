-- CommerceOps AI P3 backend-first platform hardening schema extensions
-- Adds normalized runtime failure/traceability metadata and cross-flow job attempt history.

alter table commerce_ops.sync_runs
  add column if not exists trace_id text null,
  add column if not exists failure_class text null,
  add column if not exists failure_code text null,
  add column if not exists last_error_at timestamptz null,
  add column if not exists next_retry_at timestamptz null,
  add column if not exists max_retries integer not null default 0,
  add column if not exists attempt_count integer not null default 0,
  add column if not exists terminal_failed_at timestamptz null;

alter table commerce_ops.workflow_runs
  add column if not exists trace_id text null,
  add column if not exists failure_class text null,
  add column if not exists failure_code text null,
  add column if not exists last_error_at timestamptz null,
  add column if not exists next_retry_at timestamptz null,
  add column if not exists max_retries integer not null default 0,
  add column if not exists attempt_count integer not null default 0,
  add column if not exists terminal_failed_at timestamptz null;

alter table commerce_ops.agent_runs
  add column if not exists trace_id text null,
  add column if not exists failure_class text null,
  add column if not exists failure_code text null,
  add column if not exists last_error_at timestamptz null,
  add column if not exists next_retry_at timestamptz null,
  add column if not exists max_retries integer not null default 0,
  add column if not exists attempt_count integer not null default 0,
  add column if not exists terminal_failed_at timestamptz null;

alter table commerce_ops.approval_requests
  add column if not exists trace_id text null,
  add column if not exists failure_class text null,
  add column if not exists failure_code text null,
  add column if not exists last_error_at timestamptz null,
  add column if not exists next_retry_at timestamptz null,
  add column if not exists max_retries integer not null default 0,
  add column if not exists attempt_count integer not null default 0,
  add column if not exists terminal_failed_at timestamptz null;

alter table commerce_ops.notification_deliveries
  add column if not exists trace_id text null,
  add column if not exists failure_class text null,
  add column if not exists failure_code text null,
  add column if not exists last_error_at timestamptz null,
  add column if not exists next_retry_at timestamptz null,
  add column if not exists max_retries integer not null default 0,
  add column if not exists terminal_failed_at timestamptz null;

create table if not exists commerce_ops.job_attempts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid null references commerce_ops.organizations(id) on delete cascade,
  store_id uuid null references commerce_ops.stores(id) on delete cascade,
  subject_type text not null,
  subject_id uuid not null,
  attempt_number integer not null default 1,
  status text not null default 'running',
  failure_class text null,
  failure_code text null,
  error_message text null,
  trace_id text null,
  scheduled_retry_at timestamptz null,
  duration_ms integer null,
  started_at timestamptz not null default timezone('utc', now()),
  finished_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists sync_runs_trace_idx
  on commerce_ops.sync_runs (store_id, trace_id, created_at desc);

create index if not exists workflow_runs_trace_idx
  on commerce_ops.workflow_runs (store_id, trace_id, created_at desc);

create index if not exists agent_runs_trace_idx
  on commerce_ops.agent_runs (store_id, trace_id, created_at desc);

create index if not exists approval_requests_trace_idx
  on commerce_ops.approval_requests (store_id, trace_id, created_at desc);

create index if not exists notification_deliveries_trace_idx
  on commerce_ops.notification_deliveries (store_id, trace_id, created_at desc);

create index if not exists job_attempts_subject_created_idx
  on commerce_ops.job_attempts (subject_type, subject_id, created_at desc);
