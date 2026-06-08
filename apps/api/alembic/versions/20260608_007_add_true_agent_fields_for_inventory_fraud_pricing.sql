-- CommerceOps AI true-agent schema extensions for inventory, fraud, and pricing.
-- Adds agent linkage, rationale, explanation, and review metadata to the
-- business tables that surface agent outputs.

alter table commerce_ops.reorder_suggestions
  add column if not exists agent_run_id uuid null references commerce_ops.agent_runs(id) on delete set null,
  add column if not exists rationale_summary text null,
  add column if not exists urgency text null,
  add column if not exists confidence_score numeric(5,4) null,
  add column if not exists needs_human_review boolean not null default false,
  add column if not exists review_reason_code text null;

create index if not exists reorder_suggestions_agent_run_idx
  on commerce_ops.reorder_suggestions (agent_run_id);

alter table commerce_ops.risk_reviews
  add column if not exists agent_run_id uuid null references commerce_ops.agent_runs(id) on delete set null,
  add column if not exists explanation_json jsonb not null default '{}'::jsonb,
  add column if not exists explanation_summary text null,
  add column if not exists confidence_score numeric(5,4) null,
  add column if not exists needs_human_review boolean not null default false,
  add column if not exists review_reason_code text null,
  add column if not exists recommended_decision text null;

create index if not exists risk_reviews_agent_run_idx
  on commerce_ops.risk_reviews (agent_run_id);

alter table commerce_ops.price_recommendations
  add column if not exists agent_run_id uuid null references commerce_ops.agent_runs(id) on delete set null,
  add column if not exists explanation_summary text null,
  add column if not exists confidence_score numeric(5,4) null,
  add column if not exists needs_human_review boolean not null default false,
  add column if not exists review_reason_code text null;

create index if not exists price_recommendations_agent_run_idx
  on commerce_ops.price_recommendations (agent_run_id);
