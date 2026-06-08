from uuid import UUID

from sqlalchemy import func, select

from app.core.errors import AppError
from app.core.settings import get_settings
from app.repositories.store_repository import StoreRepository
from app.repositories.workflow_repository import WorkflowRepository

from .agent_runs import get_agent_run, list_agent_runs
from .audit_events import list_audit_events
from .summary import get_summary
from .workflow_runs import get_workflow_run, list_workflow_runs, retry_workflow_run


class DashboardModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.settings = get_settings()

    def get_summary(self, user_context: dict, store_id: UUID) -> dict:
        return get_summary(self, user_context, store_id)

    def list_workflow_runs(self, user_context: dict, store_id: UUID, *, status: str | None = None, workflow_key: str | None = None, trigger_type: str | None = None) -> list[dict]:
        return list_workflow_runs(self, user_context, store_id, status=status, workflow_key=workflow_key, trigger_type=trigger_type)

    def get_workflow_run(self, user_context: dict, store_id: UUID, workflow_run_id: UUID) -> dict:
        return get_workflow_run(self, user_context, store_id, workflow_run_id)

    def retry_workflow_run(self, user_context: dict, store_id: UUID, workflow_run_id: UUID, trace_id: str | None = None) -> dict:
        return retry_workflow_run(self, user_context, store_id, workflow_run_id, trace_id=trace_id)

    def list_agent_runs(self, user_context: dict, store_id: UUID, *, agent_type: str | None = None, status: str | None = None, workflow_run_id: UUID | None = None) -> list[dict]:
        return list_agent_runs(self, user_context, store_id, agent_type=agent_type, status=status, workflow_run_id=workflow_run_id)

    def get_agent_run(self, user_context: dict, store_id: UUID, agent_run_id: UUID) -> dict:
        return get_agent_run(self, user_context, store_id, agent_run_id)

    def list_audit_events(self, user_context: dict, store_id: UUID, *, entity_type: str | None = None, action_type: str | None = None, user_id: UUID | None = None) -> list[dict]:
        return list_audit_events(self, user_context, store_id, entity_type=entity_type, action_type=action_type, user_id=user_id)

    def count_low_inventory(self, store_id: UUID) -> int:
        from app.repositories.models import ProductVariant

        count = self.db.scalar(
            select(func.count())
            .select_from(ProductVariant)
            .where(
                ProductVariant.store_id == store_id,
                ProductVariant.inventory_quantity <= self.settings.low_inventory_threshold,
            )
        )
        return count or 0

    def require_store(self, user_context: dict, store_id: UUID):
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        store = self.store_repository.get_store(UUID(organization["id"]), store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return store
