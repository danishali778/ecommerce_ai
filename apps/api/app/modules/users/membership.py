from secrets import token_urlsafe
from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission

from .serializers import serialize_user


def list_users(module, user_context: dict, status_filter: str | None, role: str | None, query: str | None) -> list[dict]:
    require_permission(user_context, Permission.USERS_MANAGE)
    organization = module.require_org(user_context)
    users = module.repository.list_by_organization(UUID(organization["id"]))
    user_ids_by_role = None
    if role:
        role_match = set()
        for user in users:
            if role in module.repository.list_role_names_for_user(user.id):
                role_match.add(user.id)
        user_ids_by_role = role_match
    results = []
    for user in users:
        if status_filter and user.status != status_filter:
            continue
        if user_ids_by_role is not None and user.id not in user_ids_by_role:
            continue
        if query and query.lower() not in f"{user.email} {user.full_name}".lower():
            continue
        results.append(serialize_user(module, user))
    return results


def create_internal_user(module, user_context: dict, payload) -> dict:
    require_permission(user_context, Permission.USERS_MANAGE)
    organization = module.require_org(user_context)
    existing = module.repository.get_by_email(payload.email)
    if existing:
        raise AppError(code="conflict", message="User already exists", status_code=409)
    auth_user = module.auth_client.admin_create_user(
        payload.email,
        f"{token_urlsafe(18)}A1!",
        {"full_name": payload.full_name},
    )
    auth_user_payload = auth_user.get("user", auth_user)
    auth_user_id = auth_user_payload.get("id")
    if not auth_user_id:
        raise AppError(code="upstream_error", message="Supabase admin create user returned no user id", status_code=502)
    user = module.repository.create(
        id=auth_user_id,
        organization_id=UUID(organization["id"]),
        email=payload.email,
        full_name=payload.full_name,
        status="invited",
    )
    roles = module.repository.get_roles_by_names(payload.role_names)
    module.repository.replace_user_roles(user.id, [role.id for role in roles], UUID(user_context["user"]["id"]))
    module.db.commit()
    return serialize_user(module, user)


def update_internal_user(module, user_context: dict, user_id: str, payload) -> dict:
    require_permission(user_context, Permission.USERS_MANAGE)
    organization = module.require_org(user_context)
    user = module.repository.get_by_id(UUID(user_id))
    if user is None or str(user.organization_id) != organization["id"]:
        raise AppError(code="not_found", message="User not found", status_code=404)
    updates = {k: v for k, v in payload.model_dump(exclude_none=True).items() if k != "role_names"}
    user = module.repository.update(user, **updates)
    if payload.role_names is not None:
        roles = module.repository.get_roles_by_names(payload.role_names)
        module.repository.replace_user_roles(user.id, [role.id for role in roles], UUID(user_context["user"]["id"]))
    module.db.commit()
    return serialize_user(module, user)

