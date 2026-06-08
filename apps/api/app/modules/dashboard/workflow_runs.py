from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission

from .serializers import serialize_workflow_run


def list_workflow_runs(module, user_context: dict, store_id: UUID, *, status: str | None = None, workflow_key: str | None = None, trigger_type: str | None = None) -> list[dict]:
    require_permission(user_context, Permission.LOGS_READ)
    store = module.require_store(user_context, store_id)
    runs = module.workflow_repository.list_workflow_runs(
        store.organization_id,
        store.id,
        status=status,
        workflow_key=workflow_key,
        trigger_type=trigger_type,
    )
    return [serialize_workflow_run(run) for run in runs]


def get_workflow_run(module, user_context: dict, store_id: UUID, workflow_run_id: UUID) -> dict:
    require_permission(user_context, Permission.LOGS_READ)
    store = module.require_store(user_context, store_id)
    run = module.workflow_repository.get_workflow_run(store.organization_id, store.id, workflow_run_id)
    if run is None:
        raise AppError(code="not_found", message="Workflow run not found", status_code=404)
    return serialize_workflow_run(run)


def retry_workflow_run(module, user_context: dict, store_id: UUID, workflow_run_id: UUID, trace_id: str | None = None) -> dict:
    require_permission(user_context, Permission.WORKFLOWS_MANAGE)
    store = module.require_store(user_context, store_id)
    run = module.workflow_repository.get_workflow_run(store.organization_id, store.id, workflow_run_id)
    if run is None:
        raise AppError(code="not_found", message="Workflow run not found", status_code=404)
    if run.status != "failed":
        raise AppError(code="conflict", message="Only failed workflow runs can be retried", status_code=409)
    module.workflow_repository.update_workflow_run(
        run,
        status="queued",
        trace_id=trace_id or run.trace_id,
        error_message=None,
        next_retry_at=None,
        terminal_failed_at=None,
    )
    module.db.commit()
    response = serialize_workflow_run(run)
    response["_enqueue_workflow_run"] = True
    return response

