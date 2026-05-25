from uuid import UUID

from app.core.authz import require_any_permission, require_permission
from app.core.errors import AppError
from app.core.permissions import Permission

from .serializers import serialize_store


def create_store(module, user_context: dict, payload) -> dict:
    require_permission(user_context, Permission.STORES_MANAGE)
    organization = module.require_org(user_context)
    stores = module.store_repository.list_stores(UUID(organization["id"]))
    if stores:
        raise AppError(code="conflict", message="P0 supports one active store only", status_code=409)
    store = module.store_repository.create_store(
        organization_id=UUID(organization["id"]),
        platform=payload.platform,
        name=payload.name,
        domain=payload.domain,
        currency=payload.currency,
        timezone=payload.timezone,
        connection_status="pending",
    )
    module.db.commit()
    return serialize_store(store)


def list_stores(module, user_context: dict) -> list[dict]:
    require_any_permission(
        user_context,
        [
            Permission.STORES_MANAGE,
            Permission.SYNC_READ,
            Permission.CATALOG_READ,
            Permission.LOGS_READ,
            Permission.NOTIFICATIONS_READ,
        ],
    )
    organization = module.require_org(user_context)
    stores = module.store_repository.list_stores(UUID(organization["id"]))
    return [serialize_store(store) for store in stores]


def get_store(module, user_context: dict, store_id) -> dict:
    require_any_permission(
        user_context,
        [
            Permission.STORES_MANAGE,
            Permission.SYNC_READ,
            Permission.CATALOG_READ,
            Permission.LOGS_READ,
            Permission.NOTIFICATIONS_READ,
        ],
    )
    store = module.require_store(user_context, store_id)
    return serialize_store(store)


def get_integration(module, user_context: dict, store_id) -> dict:
    require_permission(user_context, Permission.INTEGRATIONS_MANAGE)
    store = module.require_store(user_context, store_id)
    integration = module.store_repository.get_integration(store.id)
    if integration is None:
        raise AppError(code="not_found", message="Integration not found", status_code=404)
    return {
        "provider": integration.provider,
        "scopes": integration.scopes,
        "status": integration.status,
        "last_successful_sync_at": integration.last_successful_sync_at.isoformat() if integration.last_successful_sync_at else None,
    }

