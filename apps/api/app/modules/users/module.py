from app.core.errors import AppError
from app.integrations.supabase_auth import SupabaseAuthClient
from app.repositories.user_repository import UserRepository

from .membership import create_internal_user, list_users, update_internal_user
from .roles import list_roles


class UserModule:
    def __init__(self, db) -> None:
        self.db = db
        self.repository = UserRepository(db)
        self.auth_client = SupabaseAuthClient()

    def list_users(self, user_context: dict, status_filter: str | None, role: str | None, query: str | None) -> list[dict]:
        return list_users(self, user_context, status_filter, role, query)

    def create_internal_user(self, user_context: dict, payload) -> dict:
        return create_internal_user(self, user_context, payload)

    def update_internal_user(self, user_context: dict, user_id: str, payload) -> dict:
        return update_internal_user(self, user_context, user_id, payload)

    def list_roles(self, user_context: dict) -> list[dict]:
        return list_roles(self, user_context)

    @staticmethod
    def require_org(user_context: dict) -> dict:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        return organization
