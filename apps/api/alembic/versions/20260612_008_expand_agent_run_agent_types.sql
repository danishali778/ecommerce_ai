-- Expand allowed agent_run agent_type values to match current code.

alter table commerce_ops.agent_runs
  drop constraint if exists agent_runs_agent_type_check;

alter table commerce_ops.agent_runs
  add constraint agent_runs_agent_type_check
  check (
    agent_type in (
      'product_content',
      'support',
      'support_reply',
      'inventory',
      'inventory_reorder',
      'fraud_risk',
      'pricing',
      'pricing_recommendation',
      'analytics'
    )
  );
