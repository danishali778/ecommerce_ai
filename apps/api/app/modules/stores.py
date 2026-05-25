from __future__ import annotations

from secrets import token_urlsafe
from datetime import datetime, timezone
from uuid import UUID

from app.core.authz import require_any_permission, require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.core.secret_store import get_secret_store
from app.integrations.shopify import ShopifyClient
from app.repositories.models import Store
from app.repositories.oauth_repository import OauthRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.workflow_repository import WorkflowRepository


class StoreModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.oauth_repository = OauthRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.shopify_client = ShopifyClient()
        self.secret_store = get_secret_store()

    def create_store(self, user_context: dict, payload) -> dict:
        require_permission(user_context, Permission.STORES_MANAGE)
        organization = self._require_org(user_context)
        stores = self.store_repository.list_stores(UUID(organization["id"]))
        if stores:
            raise AppError(code="conflict", message="P0 supports one active store only", status_code=409)
        store = self.store_repository.create_store(
            organization_id=UUID(organization["id"]),
            platform=payload.platform,
            name=payload.name,
            domain=payload.domain,
            currency=payload.currency,
            timezone=payload.timezone,
            connection_status="pending",
        )
        self.db.commit()
        return self._serialize_store(store)

    def list_stores(self, user_context: dict) -> list[dict]:
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
        organization = self._require_org(user_context)
        stores = self.store_repository.list_stores(UUID(organization["id"]))
        return [self._serialize_store(store) for store in stores]

    def get_store(self, user_context: dict, store_id: UUID) -> dict:
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
        store = self._require_store(user_context, store_id)
        return self._serialize_store(store)

    def generate_install_url(self, user_context: dict, store_id: UUID, redirect_uri: str) -> dict:
        require_permission(user_context, Permission.INTEGRATIONS_MANAGE)
        store = self._require_store(user_context, store_id)
        state = token_urlsafe(32)
        self.oauth_repository.create_session(
            organization_id=store.organization_id,
            store_id=store.id,
            requested_by_user_id=UUID(user_context["user"]["id"]),
            state_nonce=state,
            redirect_uri=redirect_uri,
            expires_at=datetime.now(timezone.utc) + self._oauth_ttl(),
        )
        install_url = self.shopify_client.build_install_url(store.domain, state=state, redirect_uri=redirect_uri)
        self.db.commit()
        return {"install_url": install_url, "state": state}

    def handle_callback(self, shop: str, code: str, state: str, hmac_value: str, query_params: dict[str, str]) -> dict:
        if not self.shopify_client.verify_hmac(query_params, hmac_value):
            raise AppError(code="validation_error", message="Invalid Shopify callback HMAC", status_code=422)
        oauth_session = self.oauth_repository.get_by_state_nonce(state)
        if oauth_session is None:
            raise AppError(code="validation_error", message="Invalid Shopify callback state", status_code=422)
        now = datetime.now(timezone.utc)
        if oauth_session.used_at is not None or oauth_session.expires_at < now:
            raise AppError(code="validation_error", message="Expired or used Shopify callback state", status_code=422)
        store = self.db.query(Store).filter(Store.id == oauth_session.store_id).one_or_none()
        if store is None:
            raise AppError(code="not_found", message="Store not found for Shopify callback", status_code=404)
        if store.domain != shop:
            raise AppError(code="validation_error", message="Shopify callback shop does not match expected store", status_code=422)
        token_payload = self.shopify_client.exchange_code_for_token(shop, code)
        integration = self.store_repository.get_integration(store.id)
        scopes = token_payload.get("scope", "").split(",") if token_payload.get("scope") else []
        access_token = token_payload.get("access_token")
        if not access_token:
            raise AppError(code="upstream_error", message="Shopify token exchange returned no access token", status_code=502)
        if integration is None:
            secret_reference = self.secret_store.put(access_token)
            integration = self.store_repository.create_integration(
                organization_id=store.organization_id,
                store_id=store.id,
                provider="shopify",
                provider_account_id=shop,
                secret_reference=secret_reference,
                scopes=scopes,
                status="connected",
                last_successful_sync_at=None,
            )
        else:
            secret_reference = self.secret_store.rotate(integration.secret_reference or token_urlsafe(8), access_token)
            self.store_repository.update_integration(
                integration,
                provider_account_id=shop,
                secret_reference=secret_reference,
                scopes=scopes,
                status="connected",
            )
        self.store_repository.update_store(store, connection_status="connected")
        self.oauth_repository.mark_used(oauth_session, used_at=now)
        self.workflow_repository.create_audit_event(
            organization_id=store.organization_id,
            store_id=store.id,
            user_id=oauth_session.requested_by_user_id,
            entity_type="integration",
            entity_id=integration.id,
            action_type="shopify_connected",
            source_type="shopify_oauth",
            outcome="succeeded",
            metadata_json={"shop": shop},
        )
        self.db.commit()
        return {"store_id": str(store.id), "integration_status": "connected"}

    def get_integration(self, user_context: dict, store_id: UUID) -> dict:
        require_permission(user_context, Permission.INTEGRATIONS_MANAGE)
        store = self._require_store(user_context, store_id)
        integration = self.store_repository.get_integration(store.id)
        if integration is None:
            raise AppError(code="not_found", message="Integration not found", status_code=404)
        return {
            "provider": integration.provider,
            "scopes": integration.scopes,
            "status": integration.status,
            "last_successful_sync_at": integration.last_successful_sync_at.isoformat() if integration.last_successful_sync_at else None,
        }

    @staticmethod
    def _oauth_ttl():
        from datetime import timedelta

        return timedelta(minutes=10)

    def _require_store(self, user_context: dict, store_id: UUID):
        organization = self._require_org(user_context)
        store = self.store_repository.get_store(UUID(organization["id"]), store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return store

    @staticmethod
    def _require_org(user_context: dict) -> dict:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        return organization

    @staticmethod
    def _serialize_store(store) -> dict:
        return {
            "id": str(store.id),
            "name": store.name,
            "platform": store.platform,
            "domain": store.domain,
            "currency": store.currency,
            "timezone": store.timezone,
            "connection_status": store.connection_status,
            "last_successful_sync_at": store.last_successful_sync_at.isoformat() if store.last_successful_sync_at else None,
            "created_at": store.created_at.isoformat(),
            "updated_at": store.updated_at.isoformat(),
        }
