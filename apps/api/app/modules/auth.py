from __future__ import annotations

from secrets import token_urlsafe
from uuid import UUID

from app.core.errors import AppError
from app.core.permissions import ROLE_PERMISSION_MAP, resolve_permissions
from app.integrations.supabase_auth import SupabaseAuthClient
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.user_repository import UserRepository


class AuthModule:
    def __init__(self, db, auth_client: SupabaseAuthClient) -> None:
        self.db = db
        self.auth_client = auth_client
        self.user_repository = UserRepository(db)
        self.organization_repository = OrganizationRepository(db)
        self.store_repository = StoreRepository(db)

    def register(self, payload) -> dict:
        auth_result = self.auth_client.sign_up(payload.email, payload.password, {"full_name": payload.full_name})
        user = auth_result.get("user") or {}
        app_user = self.user_repository.get_by_email(payload.email)
        if app_user is None and user.get("id"):
            app_user = self.user_repository.create(
                id=user["id"],
                organization_id=None,
                email=payload.email,
                full_name=payload.full_name,
                status="active",
            )
            self.db.commit()
        return {
            "access_token": auth_result.get("access_token"),
            "refresh_token": auth_result.get("refresh_token"),
            "token_type": auth_result.get("token_type", "bearer"),
            "expires_in": auth_result.get("expires_in", 3600),
            "user": {
                "id": user.get("id"),
                "email": user.get("email", payload.email),
                "full_name": payload.full_name,
                "app_user_id": str(app_user.id) if app_user else None,
            },
            "organization": None,
            "available_roles": [],
        }

    def login(self, payload) -> dict:
        auth_result = self.auth_client.sign_in(payload.email, payload.password)
        user_info = auth_result.get("user") or {}
        app_user = self.user_repository.get_by_email(payload.email)
        if app_user is None and user_info.get("id"):
            app_user = self.user_repository.create(
                id=user_info["id"],
                organization_id=None,
                email=payload.email,
                full_name=(user_info.get("user_metadata") or {}).get("full_name", ""),
                status="active",
            )
        roles = self.user_repository.list_role_names_for_user(app_user.id) if app_user else []
        organization = self.organization_repository.get_by_id(app_user.organization_id) if app_user and app_user.organization_id else None
        if app_user:
            self._ensure_user_is_active(app_user.status)
            self.user_repository.update(app_user, last_login_at=user_info.get("last_sign_in_at"))
            self.db.commit()
        return {
            "access_token": auth_result.get("access_token"),
            "refresh_token": auth_result.get("refresh_token"),
            "token_type": auth_result.get("token_type", "bearer"),
            "expires_in": auth_result.get("expires_in", 3600),
            "user": {
                "id": user_info.get("id"),
                "email": user_info.get("email", payload.email),
                "full_name": app_user.full_name if app_user else "",
                "status": app_user.status if app_user else "invited",
            },
            "organization": self._serialize_organization(organization) if organization else None,
            "available_roles": roles,
        }

    def refresh(self, refresh_token: str | None) -> dict:
        if not refresh_token:
            raise AppError(code="unauthenticated", message="Missing refresh token", status_code=401)
        result = self.auth_client.refresh(refresh_token)
        return {
            "access_token": result.get("access_token"),
            "refresh_token": result.get("refresh_token"),
            "token_type": result.get("token_type", "bearer"),
            "expires_in": result.get("expires_in", 3600),
        }

    def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        refreshed = self.auth_client.refresh(refresh_token)
        access_token = refreshed.get("access_token")
        if access_token:
            self.auth_client.sign_out(access_token)

    def get_current_user_context(self, access_token: str) -> dict:
        user_info = self.auth_client.get_user(access_token)
        auth_user = user_info.get("user") or user_info
        if not auth_user or not auth_user.get("email"):
            raise AppError(code="unauthenticated", message="Invalid session", status_code=401)
        app_user = self.user_repository.get_by_email(auth_user["email"])
        if not app_user:
            app_user = self.user_repository.create(
                id=auth_user["id"],
                organization_id=None,
                email=auth_user["email"],
                full_name=auth_user.get("user_metadata", {}).get("full_name", ""),
                status="active",
            )
            self.db.commit()
        self._ensure_user_is_active(app_user.status)
        organization = self.organization_repository.get_by_id(app_user.organization_id) if app_user.organization_id else None
        roles = self.user_repository.list_role_names_for_user(app_user.id)
        permissions = resolve_permissions(roles)
        stores = self.store_repository.list_stores(app_user.organization_id) if app_user.organization_id else []
        return {
            "user": {
                "id": str(app_user.id),
                "email": app_user.email,
                "full_name": app_user.full_name,
                "status": app_user.status,
            },
            "organization": self._serialize_organization(organization) if organization else None,
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
            "available_role_summaries": self._role_summaries(),
        }

    @staticmethod
    def _serialize_organization(organization) -> dict:
        return {
            "id": str(organization.id),
            "name": organization.name,
            "slug": organization.slug,
            "status": organization.status,
        }

    @staticmethod
    def _ensure_user_is_active(status: str) -> None:
        if status in {"suspended", "disabled"}:
            raise AppError(code="forbidden", message="User account is not active", status_code=403)

    def create_random_temporary_password(self) -> str:
        return f"{token_urlsafe(18)}A1!"

    def _role_summaries(self) -> list[dict]:
        return [
            {
                "name": role.name,
                "description": role.description,
                "permissions": ROLE_PERMISSION_MAP.get(role.name, []),
            }
            for role in self.user_repository.list_roles()
        ]
