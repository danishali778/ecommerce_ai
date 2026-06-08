from __future__ import annotations

from uuid import UUID

from app.core.errors import AppError
from app.core.secret_store import get_secret_store
from app.integrations.shopify import ShopifyClient
from app.modules.fraud import FraudModule
from app.modules.inventory import InventoryModule
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workflow_repository import WorkflowRepository

from .execution import execute_sync_run
from .lifecycle import create_sync_run, get_sync_run, list_sync_runs, retry_sync_run
from .scheduling import schedule_all_store_syncs


class SyncModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.sync_repository = SyncRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.idempotency_repository = IdempotencyRepository(db)
        self.user_repository = UserRepository(db)
        self.shopify_client = ShopifyClient()
        self.secret_store = get_secret_store()
        self.fraud_module = FraudModule(db)
        self.inventory_module = InventoryModule(db)

    def create_sync_run(self, user_context: dict, store_id: UUID, mode: str, idempotency_key: str | None, trace_id: str | None = None) -> dict:
        return create_sync_run(self, user_context, store_id, mode, idempotency_key, trace_id=trace_id)

    def list_sync_runs(self, user_context: dict, store_id: UUID) -> list[dict]:
        return list_sync_runs(self, user_context, store_id)

    def get_sync_run(self, user_context: dict, store_id: UUID, sync_run_id: UUID) -> dict:
        return get_sync_run(self, user_context, store_id, sync_run_id)

    def retry_sync_run(self, user_context: dict, store_id: UUID, sync_run_id: UUID, idempotency_key: str | None, trace_id: str | None = None) -> dict:
        return retry_sync_run(self, user_context, store_id, sync_run_id, idempotency_key, trace_id=trace_id)

    def execute_sync_run(self, sync_run_id: str, trace_id: str | None = None) -> None:
        execute_sync_run(self, sync_run_id, trace_id=trace_id)

    def schedule_all_store_syncs(self) -> list[str]:
        return schedule_all_store_syncs(self)

    def require_store(self, user_context: dict, store_id: UUID):
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        store = self.store_repository.get_store(UUID(organization["id"]), store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return store
