from __future__ import annotations

from secrets import token_urlsafe

from app.core.permissions import ROLE_PERMISSION_MAP, resolve_permissions
from app.integrations.supabase_auth import SupabaseAuthClient
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.user_repository import UserRepository

from .registration import register
from .sessions import login, logout, refresh
from .user_context import get_current_user_context


class AuthModule:
    def __init__(self, db, auth_client: SupabaseAuthClient) -> None:
        self.db = db
        self.auth_client = auth_client
        self.user_repository = UserRepository(db)
        self.organization_repository = OrganizationRepository(db)
        self.store_repository = StoreRepository(db)
        self.resolve_permissions = resolve_permissions

    def register(self, payload) -> dict:
        return register(self, payload)

    def login(self, payload) -> dict:
        return login(self, payload)

    def refresh(self, refresh_token: str | None) -> dict:
        return refresh(self, refresh_token)

    def logout(self, refresh_token: str | None) -> None:
        logout(self, refresh_token)

    def get_current_user_context(self, access_token: str) -> dict:
        return get_current_user_context(self, access_token)

    def create_random_temporary_password(self) -> str:
        return f"{token_urlsafe(18)}A1!"

    def role_summaries(self) -> list[dict]:
        return [
            {
                "name": role.name,
                "description": role.description,
                "permissions": ROLE_PERMISSION_MAP.get(role.name, []),
            }
            for role in self.user_repository.list_roles()
        ]
