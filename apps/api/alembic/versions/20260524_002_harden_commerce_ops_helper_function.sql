-- CommerceOps AI P0 helper-function hardening
-- Aligns the live trigger helper with the repo migration definition.

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
