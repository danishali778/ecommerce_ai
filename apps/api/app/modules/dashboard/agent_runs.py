from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission

from .serializers import serialize_agent_run


def list_agent_runs(module, user_context: dict, store_id: UUID, *, agent_type: str | None = None, status: str | None = None, workflow_run_id: UUID | None = None) -> list[dict]:
    require_permission(user_context, Permission.LOGS_READ)
    store = module.require_store(user_context, store_id)
    runs = module.workflow_repository.list_agent_runs(
        store.organization_id,
        store.id,
        agent_type=agent_type,
        status=status,
        workflow_run_id=workflow_run_id,
    )
    return [serialize_agent_run(run) for run in runs]


def get_agent_run(module, user_context: dict, store_id: UUID, agent_run_id: UUID) -> dict:
    require_permission(user_context, Permission.LOGS_READ)
    store = module.require_store(user_context, store_id)
    run = module.workflow_repository.get_agent_run(store.organization_id, store.id, agent_run_id)
    if run is None:
        raise AppError(code="not_found", message="Agent run not found", status_code=404)
    return serialize_agent_run(run)

