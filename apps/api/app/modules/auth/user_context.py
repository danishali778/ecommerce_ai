from .registration import ensure_user_is_active
from .serializers import serialize_organization


def get_current_user_context(module, access_token: str) -> dict:
    user_info = module.auth_client.get_user(access_token)
    auth_user = user_info.get("user") or user_info
    if not auth_user or not auth_user.get("email"):
        from app.core.errors import AppError

        raise AppError(code="unauthenticated", message="Invalid session", status_code=401)
    app_user = module.user_repository.get_by_email(auth_user["email"])
    if not app_user:
        app_user = module.user_repository.create(
            id=auth_user["id"],
            organization_id=None,
            email=auth_user["email"],
            full_name=auth_user.get("user_metadata", {}).get("full_name", ""),
            status="active",
        )
        module.db.commit()
    ensure_user_is_active(app_user.status)
    organization = module.organization_repository.get_by_id(app_user.organization_id) if app_user.organization_id else None
    roles = module.user_repository.list_role_names_for_user(app_user.id)
    permissions = module.resolve_permissions(roles)
    stores = module.store_repository.list_stores(app_user.organization_id) if app_user.organization_id else []
    return {
        "user": {
            "id": str(app_user.id),
            "email": app_user.email,
            "full_name": app_user.full_name,
            "status": app_user.status,
        },
        "organization": serialize_organization(organization) if organization else None,
        "roles": roles,
        "permissions": permissions,
        "accessible_stores": [
            {
                "id": str(store.id),
                "name": store.name,
                "platform": store.platform,
                "domain": store.domain,
                "currency": store.currency,
                "timezone": store.timezone,
                "connection_status": store.connection_status,
                "last_successful_sync_at": store.last_successful_sync_at.isoformat() if store.last_successful_sync_at else None,
                "created_at": store.created_at,
                "updated_at": store.updated_at,
            }
            for store in stores
        ],
        "available_role_summaries": module.role_summaries(),
    }

