from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select

from app.core.authz import require_any_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.repositories.models import (
    AgentRun,
    ApprovalRequest,
    InventoryAlert,
    Order,
    ReorderSuggestion,
    RiskReview,
    SupportConversation,
    SupportMessage,
    SyncRun,
    WorkflowRun,
)
from app.repositories.store_repository import StoreRepository


class AnalyticsModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)

    def get_overview(self, user_context: dict, store_id: UUID, *, date_from=None, date_to=None) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.ANALYTICS_READ, Permission.LOGS_READ])
        start_at, end_at = self.resolve_range(date_from, date_to)
        sections: dict[str, dict] = {}
        partial_errors: list[dict] = []

        def run_section(name: str, builder):
            try:
                sections[name] = builder()
            except Exception as exc:  # noqa: BLE001
                partial_errors.append({"section": name, "message": str(exc)})

        run_section(
            "sales",
            lambda: {
                "order_count": self.scalar_count(Order, organization_id, store_id, start_at, end_at),
                "gross_sales_total": self.scalar_sum(Order.total, Order, organization_id, store_id, start_at, end_at),
                "average_order_value": self.scalar_avg(Order.total, Order, organization_id, store_id, start_at, end_at),
            },
        )
        run_section(
            "inventory",
            lambda: {
                "open_low_stock_alert_count": self.status_count(InventoryAlert, organization_id, store_id, "status", "open"),
                "open_reorder_suggestion_count": self.status_count(ReorderSuggestion, organization_id, store_id, "status", "open"),
            },
        )
        run_section(
            "support",
            lambda: {
                "open_conversation_count": self.status_count(SupportConversation, organization_id, store_id, "status", "open"),
                "pending_support_review_count": self.status_count(SupportConversation, organization_id, store_id, "status", "pending_review"),
                "support_drafts_generated_count": self.scalar_count(
                    SupportMessage,
                    organization_id,
                    store_id,
                    start_at,
                    end_at,
                    extra_filters=(SupportMessage.generated_by_ai.is_(True),),
                ),
            },
        )
        run_section(
            "fraud",
            lambda: {
                "high_risk_order_count": self.status_count(Order, organization_id, store_id, "risk_status", "high_risk"),
                "pending_risk_review_count": self.status_count(RiskReview, organization_id, store_id, "risk_status", "pending_review"),
            },
        )
        run_section(
            "operations",
            lambda: {
                "latest_sync_status": self.latest_sync_status(organization_id, store_id),
                "latest_sync_completed_at": self.latest_sync_completed_at(organization_id, store_id),
                "pending_approval_count": self.status_count(ApprovalRequest, organization_id, store_id, "status", "pending"),
            },
        )
        payload = {
            "range": {"date_from": start_at.isoformat(), "date_to": end_at.isoformat()},
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": sections,
        }
        if partial_errors:
            payload["partial_errors"] = partial_errors
        return payload

    def get_automation(self, user_context: dict, store_id: UUID, *, date_from=None, date_to=None) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.ANALYTICS_READ, Permission.LOGS_READ])
        start_at, end_at = self.resolve_range(date_from, date_to)
        payload = {
            "range": {"date_from": start_at.isoformat(), "date_to": end_at.isoformat()},
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": {
                "automation": {
                    "workflow_runs_total": self.scalar_count(WorkflowRun, organization_id, store_id, start_at, end_at),
                    "workflow_failures_total": self.scalar_count(
                        WorkflowRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(WorkflowRun.status == "failed",),
                    ),
                    "agent_runs_total": self.scalar_count(AgentRun, organization_id, store_id, start_at, end_at),
                    "agent_runs_failed": self.scalar_count(
                        AgentRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(AgentRun.status == "failed",),
                    ),
                    "product_content_drafts_generated_count": self.scalar_count(
                        AgentRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(AgentRun.agent_type == "product_content",),
                    ),
                    "support_drafts_generated_count": self.scalar_count(
                        AgentRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(AgentRun.agent_type == "support_reply",),
                    ),
                }
            },
        }
        return payload

    @staticmethod
    def resolve_range(date_from, date_to) -> tuple[datetime, datetime]:
        end_at = datetime.now(UTC)
        start_at = end_at - timedelta(days=30)
        if date_from:
            start_at = datetime.fromisoformat(date_from)
        if date_to:
            end_at = datetime.fromisoformat(date_to)
        return start_at, end_at

    def scalar_count(self, model, organization_id: UUID, store_id: UUID, start_at: datetime, end_at: datetime, *, extra_filters=()):
        query = select(func.count()).select_from(model).where(
            model.organization_id == organization_id,
            model.store_id == store_id,
            model.created_at >= start_at,
            model.created_at <= end_at,
            *extra_filters,
        )
        return int(self.db.scalar(query) or 0)

    def scalar_sum(self, column, model, organization_id: UUID, store_id: UUID, start_at: datetime, end_at: datetime) -> str:
        query = select(func.coalesce(func.sum(column), 0)).select_from(model).where(
            model.organization_id == organization_id,
            model.store_id == store_id,
            model.created_at >= start_at,
            model.created_at <= end_at,
        )
        return str(self.db.scalar(query) or 0)

    def scalar_avg(self, column, model, organization_id: UUID, store_id: UUID, start_at: datetime, end_at: datetime) -> str:
        query = select(func.coalesce(func.avg(column), 0)).select_from(model).where(
            model.organization_id == organization_id,
            model.store_id == store_id,
            model.created_at >= start_at,
            model.created_at <= end_at,
        )
        return str(self.db.scalar(query) or 0)

    def status_count(self, model, organization_id: UUID, store_id: UUID, field_name: str, value: str) -> int:
        column = getattr(model, field_name)
        query = select(func.count()).select_from(model).where(
            model.organization_id == organization_id,
            model.store_id == store_id,
            column == value,
        )
        return int(self.db.scalar(query) or 0)

    def latest_sync_status(self, organization_id: UUID, store_id: UUID) -> str | None:
        return self.db.scalar(
            select(SyncRun.status)
            .where(SyncRun.organization_id == organization_id, SyncRun.store_id == store_id)
            .order_by(SyncRun.created_at.desc())
            .limit(1)
        )

    def latest_sync_completed_at(self, organization_id: UUID, store_id: UUID) -> str | None:
        completed_at = self.db.scalar(
            select(SyncRun.completed_at)
            .where(SyncRun.organization_id == organization_id, SyncRun.store_id == store_id)
            .order_by(SyncRun.created_at.desc())
            .limit(1)
        )
        return completed_at.isoformat() if completed_at else None

    def require_store_access(self, user_context: dict, store_id: UUID) -> UUID:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        organization_id = UUID(organization["id"])
        store = self.store_repository.get_store(organization_id, store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return organization_id
