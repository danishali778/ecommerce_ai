from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.idempotency import resolve_idempotent_response
from app.core.permissions import Permission

from .serializers import serialize_sync_run


def create_sync_run(module, user_context: dict, store_id: UUID, mode: str, idempotency_key: str | None, trace_id: str | None = None) -> dict:
    require_permission(user_context, Permission.SYNC_TRIGGER)
    store = module.require_store(user_context, store_id)
    existing_response, _, fingerprint = resolve_idempotent_response(
        module.idempotency_repository,
        organization_id=store.organization_id,
        scope="sync:create",
        idempotency_key=idempotency_key,
        payload={"store_id": str(store.id), "mode": mode},
    )
    if existing_response is not None:
        return existing_response
    integration = module.store_repository.get_integration(store.id)
    if integration is None or integration.status != "connected":
        raise AppError(code="conflict", message="Store is not connected to Shopify", status_code=409)
    active = module.sync_repository.get_active_sync_run(store.id)
    if active:
        raise AppError(code="sync_in_progress", message="Another sync is already active", status_code=409)
    sync_run = module.sync_repository.create_sync_run(
        organization_id=store.organization_id,
        store_id=store.id,
        integration_id=integration.id,
        mode=mode,
        status="queued",
        trace_id=trace_id,
        triggered_by_user_id=UUID(user_context["user"]["id"]),
        entity_counts_json={},
        error_details_json={},
    )
    response = serialize_sync_run(sync_run)
    response["_enqueue_sync_run"] = True
    module.idempotency_repository.create_record(
        organization_id=store.organization_id,
        scope="sync:create",
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        resource_type="sync_run",
        resource_id=sync_run.id,
        response_json={k: v for k, v in response.items() if not k.startswith("_")},
    )
    module.db.commit()
    return response


def list_sync_runs(module, user_context: dict, store_id: UUID) -> list[dict]:
    require_permission(user_context, Permission.SYNC_READ)
    store = module.require_store(user_context, store_id)
    return [serialize_sync_run(item) for item in module.sync_repository.list_sync_runs(store.organization_id, store.id)]


def get_sync_run(module, user_context: dict, store_id: UUID, sync_run_id: UUID) -> dict:
    require_permission(user_context, Permission.SYNC_READ)
    store = module.require_store(user_context, store_id)
    sync_run = module.sync_repository.get_sync_run(store.organization_id, store.id, sync_run_id)
    if sync_run is None:
        raise AppError(code="not_found", message="Sync run not found", status_code=404)
    return serialize_sync_run(sync_run)


def retry_sync_run(module, user_context: dict, store_id: UUID, sync_run_id: UUID, idempotency_key: str | None, trace_id: str | None = None) -> dict:
    require_permission(user_context, Permission.SYNC_TRIGGER)
    store = module.require_store(user_context, store_id)
    existing_response, _, fingerprint = resolve_idempotent_response(
        module.idempotency_repository,
        organization_id=store.organization_id,
        scope=f"sync:retry:{sync_run_id}",
        idempotency_key=idempotency_key,
        payload={"store_id": str(store.id), "sync_run_id": str(sync_run_id)},
    )
    if existing_response is not None:
        return existing_response
    previous = module.sync_repository.get_sync_run(store.organization_id, store.id, sync_run_id)
    if previous is None:
        raise AppError(code="not_found", message="Sync run not found", status_code=404)
    if previous.status != "failed":
        raise AppError(code="conflict", message="Only failed syncs can be retried", status_code=409)
    integration = module.store_repository.get_integration(store.id)
    sync_run = module.sync_repository.create_sync_run(
        organization_id=store.organization_id,
        store_id=store.id,
        integration_id=integration.id,
        mode="retry_full",
        status="queued",
        trace_id=trace_id,
        triggered_by_user_id=UUID(user_context["user"]["id"]),
        retry_of_sync_run_id=previous.id,
        entity_counts_json={},
        error_details_json={},
    )
    response = serialize_sync_run(sync_run)
    response["_enqueue_sync_run"] = True
    module.idempotency_repository.create_record(
        organization_id=store.organization_id,
        scope=f"sync:retry:{sync_run_id}",
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        resource_type="sync_run",
        resource_id=sync_run.id,
        response_json={k: v for k, v in response.items() if not k.startswith("_")},
    )
    module.db.commit()
    return response

