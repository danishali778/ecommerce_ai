from uuid import UUID


def sync_failure_recipients(module, sync_run) -> list[UUID]:
    if sync_run.triggered_by_user_id:
        return [sync_run.triggered_by_user_id]
    users = module.user_repository.list_users_with_any_role(sync_run.organization_id, ["Owner", "Admin"])
    return [user.id for user in users]

