from __future__ import annotations

from uuid import UUID

from app.core.errors import AppError
from app.core.secret_store import get_secret_store
from app.integrations.shopify import ShopifyClient
from app.repositories.oauth_repository import OauthRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.workflow_repository import WorkflowRepository

from .crud import create_store, get_integration, get_store, list_stores
from .shopify_oauth import generate_install_url, handle_callback


class StoreModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.oauth_repository = OauthRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.shopify_client = ShopifyClient()
        self.secret_store = get_secret_store()

    def create_store(self, user_context: dict, payload) -> dict:
        return create_store(self, user_context, payload)

    def list_stores(self, user_context: dict) -> list[dict]:
        return list_stores(self, user_context)

    def get_store(self, user_context: dict, store_id: UUID) -> dict:
        return get_store(self, user_context, store_id)

    def generate_install_url(self, user_context: dict, store_id: UUID, redirect_uri: str) -> dict:
        return generate_install_url(self, user_context, store_id, redirect_uri)

    def handle_callback(self, shop: str, code: str, state: str, hmac_value: str, query_params: dict[str, str]) -> dict:
        return handle_callback(self, shop, code, state, hmac_value, query_params)

    def get_integration(self, user_context: dict, store_id: UUID) -> dict:
        return get_integration(self, user_context, store_id)

    def require_store(self, user_context: dict, store_id: UUID):
        organization = self.require_org(user_context)
        store = self.store_repository.get_store(UUID(organization["id"]), store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return store

    @staticmethod
    def require_org(user_context: dict) -> dict:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        return organization
