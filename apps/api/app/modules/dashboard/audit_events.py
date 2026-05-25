from uuid import UUID

from app.core.authz import require_permission
from app.core.permissions import Permission

from .serializers import serialize_audit_event


def list_audit_events(module, user_context: dict, store_id: UUID, *, entity_type: str | None = None, action_type: str | None = None, user_id: UUID | None = None) -> list[dict]:
    require_permission(user_context, Permission.LOGS_READ)
    store = module.require_store(user_context, store_id)
    events = module.workflow_repository.list_audit_events(
        store.organization_id,
        store.id,
        entity_type=entity_type,
        action_type=action_type,
        user_id=user_id,
    )
    return [serialize_audit_event(event) for event in events]

