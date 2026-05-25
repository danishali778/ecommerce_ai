from uuid import UUID

from sqlalchemy import func, select

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.core.settings import get_settings
from app.repositories.models import ApprovalRequest, AgentRun, Customer, Order, Product, SyncRun, WorkflowRun
from app.repositories.store_repository import StoreRepository
from app.repositories.workflow_repository import WorkflowRepository


class DashboardModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.settings = get_settings()

    def get_summary(self, user_context: dict, store_id: UUID) -> dict:
        require_permission(user_context, Permission.SYNC_READ)
        store = self._require_store(user_context, store_id)
        latest_sync = self.db.scalar(
            select(SyncRun).where(SyncRun.store_id == store.id).order_by(SyncRun.created_at.desc()).limit(1)
        )
        recent_workflow_failures = self.db.scalar(
            select(func.count()).select_from(WorkflowRun).where(WorkflowRun.store_id == store.id, WorkflowRun.status == "failed")
        )
        pending_approvals = self.db.scalar(
            select(func.count()).select_from(ApprovalRequest).where(ApprovalRequest.store_id == store.id, ApprovalRequest.status == "pending")
        )
        recent_agent_runs = self.db.scalar(select(func.count()).select_from(AgentRun).where(AgentRun.store_id == store.id))
        product_count = self.db.scalar(select(func.count()).select_from(Product).where(Product.store_id == store.id))
        order_count = self.db.scalar(select(func.count()).select_from(Order).where(Order.store_id == store.id))
        customer_count = self.db.scalar(select(func.count()).select_from(Customer).where(Customer.store_id == store.id))
        return {
            "latest_sync_status": latest_sync.status if latest_sync else None,
            "latest_sync_completed_at": latest_sync.completed_at.isoformat() if latest_sync and latest_sync.completed_at else None,
            "product_count": product_count or 0,
            "order_count": order_count or 0,
            "customer_count": customer_count or 0,
            "low_inventory_count": self._count_low_inventory(store.id),
            "pending_approval_count": pending_approvals or 0,
            "recent_workflow_failures": recent_workflow_failures or 0,
            "recent_agent_runs": recent_agent_runs or 0,
        }

    def list_workflow_runs(
        self,
        user_context: dict,
        store_id: UUID,
        *,
        status: str | None = None,
        workflow_key: str | None = None,
        trigger_type: str | None = None,
    ) -> list[dict]:
        require_permission(user_context, Permission.LOGS_READ)
        store = self._require_store(user_context, store_id)
        runs = self.workflow_repository.list_workflow_runs(
            store.organization_id,
            store.id,
            status=status,
            workflow_key=workflow_key,
            trigger_type=trigger_type,
        )
        return [
            {
                "id": str(run.id),
                "status": run.status,
                "trigger_type": run.trigger_type,
                "workflow_id": str(run.workflow_id) if run.workflow_id else None,
                "created_at": run.created_at.isoformat(),
                "input_payload": run.input_payload,
                "output_payload": run.output_payload,
                "error_message": run.error_message,
            }
            for run in runs
        ]

    def get_workflow_run(self, user_context: dict, store_id: UUID, workflow_run_id: UUID) -> dict:
        require_permission(user_context, Permission.LOGS_READ)
        store = self._require_store(user_context, store_id)
        run = self.workflow_repository.get_workflow_run(store.organization_id, store.id, workflow_run_id)
        if run is None:
            raise AppError(code="not_found", message="Workflow run not found", status_code=404)
        return {
            "id": str(run.id),
            "status": run.status,
            "trigger_type": run.trigger_type,
            "workflow_id": str(run.workflow_id) if run.workflow_id else None,
            "created_at": run.created_at.isoformat(),
            "input_payload": run.input_payload,
            "output_payload": run.output_payload,
            "error_message": run.error_message,
        }

    def list_agent_runs(
        self,
        user_context: dict,
        store_id: UUID,
        *,
        agent_type: str | None = None,
        status: str | None = None,
        workflow_run_id: UUID | None = None,
    ) -> list[dict]:
        require_permission(user_context, Permission.LOGS_READ)
        store = self._require_store(user_context, store_id)
        runs = self.workflow_repository.list_agent_runs(
            store.organization_id,
            store.id,
            agent_type=agent_type,
            status=status,
            workflow_run_id=workflow_run_id,
        )
        return [
            {
                "id": str(run.id),
                "status": run.status,
                "agent_type": run.agent_type,
                "model_name": run.model_name,
                "created_at": run.created_at.isoformat(),
                "workflow_run_id": str(run.workflow_run_id) if run.workflow_run_id else None,
                "input_summary": run.input_summary,
                "retrieved_context_summary": run.retrieved_context_summary,
                "output_summary": run.output_summary,
                "error_message": run.error_message,
            }
            for run in runs
        ]

    def get_agent_run(self, user_context: dict, store_id: UUID, agent_run_id: UUID) -> dict:
        require_permission(user_context, Permission.LOGS_READ)
        store = self._require_store(user_context, store_id)
        run = self.workflow_repository.get_agent_run(store.organization_id, store.id, agent_run_id)
        if run is None:
            raise AppError(code="not_found", message="Agent run not found", status_code=404)
        return {
            "id": str(run.id),
            "status": run.status,
            "agent_type": run.agent_type,
            "model_name": run.model_name,
            "created_at": run.created_at.isoformat(),
            "workflow_run_id": str(run.workflow_run_id) if run.workflow_run_id else None,
            "input_summary": run.input_summary,
            "retrieved_context_summary": run.retrieved_context_summary,
            "output_summary": run.output_summary,
            "error_message": run.error_message,
        }

    def list_audit_events(
        self,
        user_context: dict,
        store_id: UUID,
        *,
        entity_type: str | None = None,
        action_type: str | None = None,
        user_id: UUID | None = None,
    ) -> list[dict]:
        require_permission(user_context, Permission.LOGS_READ)
        store = self._require_store(user_context, store_id)
        events = self.workflow_repository.list_audit_events(
            store.organization_id,
            store.id,
            entity_type=entity_type,
            action_type=action_type,
            user_id=user_id,
        )
        return [
            {
                "id": str(event.id),
                "entity_type": event.entity_type,
                "action_type": event.action_type,
                "source_type": event.source_type,
                "outcome": event.outcome,
                "created_at": event.created_at.isoformat(),
                "user_id": str(event.user_id) if event.user_id else None,
                "metadata_json": event.metadata_json,
            }
            for event in events
        ]

    def _count_low_inventory(self, store_id: UUID) -> int:
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

    def _require_store(self, user_context: dict, store_id: UUID):
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        store = self.store_repository.get_store(UUID(organization["id"]), store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return store
