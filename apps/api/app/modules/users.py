from secrets import token_urlsafe
from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission, ROLE_PERMISSION_MAP
from app.integrations.supabase_auth import SupabaseAuthClient
from app.repositories.user_repository import UserRepository


class UserModule:
    def __init__(self, db) -> None:
        self.db = db
        self.repository = UserRepository(db)
        self.auth_client = SupabaseAuthClient()

    def list_users(self, user_context: dict, status_filter: str | None, role: str | None, query: str | None) -> list[dict]:
        require_permission(user_context, Permission.USERS_MANAGE)
        organization = self._require_org(user_context)
        users = self.repository.list_by_organization(UUID(organization["id"]))
        user_ids_by_role = None
        if role:
            role_match = set()
            for user in users:
                if role in self.repository.list_role_names_for_user(user.id):
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
            results.append(self._serialize_user(user))
        return results

    def create_internal_user(self, user_context: dict, payload) -> dict:
        require_permission(user_context, Permission.USERS_MANAGE)
        organization = self._require_org(user_context)
        existing = self.repository.get_by_email(payload.email)
        if existing:
            raise AppError(code="conflict", message="User already exists", status_code=409)
        auth_user = self.auth_client.admin_create_user(
            payload.email,
            f"{token_urlsafe(18)}A1!",
            {"full_name": payload.full_name},
        )
        auth_user_payload = auth_user.get("user", auth_user)
        auth_user_id = auth_user_payload.get("id")
        if not auth_user_id:
            raise AppError(code="upstream_error", message="Supabase admin create user returned no user id", status_code=502)
        user = self.repository.create(
            id=auth_user_id,
            organization_id=UUID(organization["id"]),
            email=payload.email,
            full_name=payload.full_name,
            status="invited",
        )
        roles = self.repository.get_roles_by_names(payload.role_names)
        self.repository.replace_user_roles(user.id, [role.id for role in roles], UUID(user_context["user"]["id"]))
        self.db.commit()
        return self._serialize_user(user)

    def update_internal_user(self, user_context: dict, user_id: str, payload) -> dict:
        require_permission(user_context, Permission.USERS_MANAGE)
        organization = self._require_org(user_context)
        user = self.repository.get_by_id(UUID(user_id))
        if user is None or str(user.organization_id) != organization["id"]:
            raise AppError(code="not_found", message="User not found", status_code=404)
        updates = {k: v for k, v in payload.model_dump(exclude_none=True).items() if k != "role_names"}
        user = self.repository.update(user, **updates)
        if payload.role_names is not None:
            roles = self.repository.get_roles_by_names(payload.role_names)
            self.repository.replace_user_roles(user.id, [role.id for role in roles], UUID(user_context["user"]["id"]))
        self.db.commit()
        return self._serialize_user(user)

    def list_roles(self, user_context: dict) -> list[dict]:
        require_permission(user_context, Permission.USERS_MANAGE)
        self._require_org(user_context)
        roles = self.repository.list_roles()
        return [
            {
                "name": role.name,
                "description": role.description,
                "permissions": ROLE_PERMISSION_MAP.get(role.name, []),
            }
            for role in roles
        ]

    @staticmethod
    def _require_org(user_context: dict) -> dict:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        return organization

    def _serialize_user(self, user) -> dict:
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "status": user.status,
            "roles": self.repository.list_role_names_for_user(user.id),
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }
