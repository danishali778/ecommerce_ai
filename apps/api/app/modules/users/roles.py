from app.core.authz import require_permission
from app.core.permissions import Permission, ROLE_PERMISSION_MAP


def list_roles(module, user_context: dict) -> list[dict]:
    require_permission(user_context, Permission.USERS_MANAGE)
    module.require_org(user_context)
    roles = module.repository.list_roles()
    return [
        {
            "name": role.name,
            "description": role.description,
            "permissions": ROLE_PERMISSION_MAP.get(role.name, []),
        }
        for role in roles
    ]

