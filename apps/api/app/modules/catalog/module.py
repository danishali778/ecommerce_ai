from __future__ import annotations

from uuid import UUID

from app.agents.product_content.runner import ProductContentAgentRunner
from app.core.errors import AppError
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workflow_repository import WorkflowRepository

from .commerce_reads import get_customer, get_order, list_customers, list_orders
from .drafts import generate_draft, get_draft, list_drafts, submit_draft_for_approval, update_draft
from .products import get_product, list_products


class CatalogModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.sync_repository = SyncRepository(db)
        self.catalog_repository = CatalogRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.approval_repository = ApprovalRepository(db)
        self.user_repository = UserRepository(db)
        self.agent_runner = ProductContentAgentRunner(db)

    def list_products(self, user_context: dict, store_id: UUID) -> list[dict]:
        return list_products(self, user_context, store_id)

    def get_product(self, user_context: dict, store_id: UUID, product_id: UUID) -> dict:
        return get_product(self, user_context, store_id, product_id)

    def list_drafts(self, user_context: dict, store_id: UUID, product_id: UUID) -> list[dict]:
        return list_drafts(self, user_context, store_id, product_id)

    def generate_draft(self, user_context: dict, store_id: UUID, product_id: UUID, payload) -> dict:
        return generate_draft(self, user_context, store_id, product_id, payload)

    def get_draft(self, user_context: dict, store_id: UUID, product_id: UUID, draft_id: UUID) -> dict:
        return get_draft(self, user_context, store_id, product_id, draft_id)

    def update_draft(self, user_context: dict, store_id: UUID, product_id: UUID, draft_id: UUID, payload) -> dict:
        return update_draft(self, user_context, store_id, product_id, draft_id, payload)

    def submit_draft_for_approval(self, user_context: dict, store_id: UUID, product_id: UUID, draft_id: UUID, reason: str, idempotency_key: str | None) -> dict:
        return submit_draft_for_approval(self, user_context, store_id, product_id, draft_id, reason, idempotency_key)

    def list_orders(self, user_context: dict, store_id: UUID) -> list[dict]:
        return list_orders(self, user_context, store_id)

    def get_order(self, user_context: dict, store_id: UUID, order_id: UUID) -> dict:
        return get_order(self, user_context, store_id, order_id)

    def list_customers(self, user_context: dict, store_id: UUID) -> list[dict]:
        return list_customers(self, user_context, store_id)

    def get_customer(self, user_context: dict, store_id: UUID, customer_id: UUID) -> dict:
        return get_customer(self, user_context, store_id, customer_id)

    def require_store(self, user_context: dict, store_id: UUID):
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        store = self.store_repository.get_store(UUID(organization["id"]), store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return store
