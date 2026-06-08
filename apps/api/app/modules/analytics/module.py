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
    NotificationChannel,
    NotificationDelivery,
    Order,
    PriceRecommendation,
    PricingRule,
    ReorderSuggestion,
    RiskReview,
    SupportConversation,
    SupportMessage,
    SyncRun,
    Workflow,
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
                "pending_retry_count": self.pending_retry_count(organization_id, store_id),
                "terminal_failure_count": self.terminal_failure_count(organization_id, store_id),
                "requires_operator_count": self.requires_operator_count(organization_id, store_id),
                "sync_queue_lag_seconds_avg": self.average_queue_lag_seconds(SyncRun, organization_id, store_id, start_at, end_at),
                "workflow_queue_lag_seconds_avg": self.average_queue_lag_seconds(WorkflowRun, organization_id, store_id, start_at, end_at),
                "sync_runtime_seconds_avg": self.average_runtime_seconds(SyncRun, organization_id, store_id, start_at, end_at),
                "workflow_runtime_seconds_avg": self.average_runtime_seconds(WorkflowRun, organization_id, store_id, start_at, end_at),
            },
        )
        run_section(
            "pricing",
            lambda: {
                "pricing_rule_count": self.scalar_count(PricingRule, organization_id, store_id, start_at, end_at),
                "pricing_recommendations_pending_approval": self.status_count(PriceRecommendation, organization_id, store_id, "status", "pending_approval"),
                "pricing_recommendations_blocked": self.status_count(PriceRecommendation, organization_id, store_id, "validation_status", "blocked"),
            },
        )
        run_section(
            "workflows",
            lambda: {
                "workflow_definition_count": self.workflow_definition_count(organization_id, store_id),
                "enabled_workflow_definition_count": self.workflow_definition_count(organization_id, store_id, is_active=True),
            },
        )
        run_section(
            "notifications",
            lambda: {
                "configured_notification_channels": self.scalar_count(NotificationChannel, organization_id, store_id, start_at, end_at),
                "notification_deliveries_failed": self.status_count(NotificationDelivery, organization_id, store_id, "status", "failed"),
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
                    "inventory_agent_runs_total": self.scalar_count(
                        AgentRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(AgentRun.agent_type == "inventory_reorder",),
                    ),
                    "fraud_agent_runs_total": self.scalar_count(
                        AgentRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(AgentRun.agent_type == "fraud_risk",),
                    ),
                    "pricing_agent_runs_total": self.scalar_count(
                        AgentRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(AgentRun.agent_type == "pricing_recommendation",),
                    ),
                    "user_defined_workflow_runs_total": self.scalar_count(
                        WorkflowRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(WorkflowRun.workflow_id.is_not(None),),
                    ),
                    "external_notification_deliveries_total": self.scalar_count(
                        NotificationDelivery,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                    ),
                    "external_notification_deliveries_failed": self.scalar_count(
                        NotificationDelivery,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(NotificationDelivery.status == "failed",),
                    ),
                    "sync_retry_total": self.scalar_sum_int(
                        SyncRun.retry_count,
                        SyncRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                    ),
                    "workflow_retry_total": self.scalar_sum_int(
                        WorkflowRun.retry_count,
                        WorkflowRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                    ),
                    "approval_retry_total": self.scalar_sum_int(
                        ApprovalRequest.retry_count,
                        ApprovalRequest,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                    ),
                    "notification_attempt_total": self.scalar_sum_int(
                        NotificationDelivery.attempt_count,
                        NotificationDelivery,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                    ),
                    "terminal_failures_total": self.terminal_failure_count(organization_id, store_id),
                    "requires_operator_failures_total": self.requires_operator_count(organization_id, store_id),
                    "workflow_runtime_seconds_avg": self.average_runtime_seconds(
                        WorkflowRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                    ),
                    "agent_runtime_seconds_avg": self.average_runtime_seconds(
                        AgentRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                    ),
                    "notification_delivery_latency_seconds_avg": self.average_notification_delivery_latency_seconds(
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                    ),
                }
            },
        }
        return payload

    def get_pricing_metrics(self, user_context: dict, store_id: UUID, *, date_from=None, date_to=None) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.ANALYTICS_READ, Permission.PRICING_READ, Permission.PRICING_MANAGE])
        start_at, end_at = self.resolve_range(date_from, date_to)
        return {
            "range": {"date_from": start_at.isoformat(), "date_to": end_at.isoformat()},
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": {
                "pricing": {
                    "pricing_rule_count": self.scalar_count(PricingRule, organization_id, store_id, start_at, end_at),
                    "recommendations_total": self.scalar_count(PriceRecommendation, organization_id, store_id, start_at, end_at),
                    "recommendations_pending_approval": self.status_count(PriceRecommendation, organization_id, store_id, "status", "pending_approval"),
                    "recommendations_approved": self.status_count(PriceRecommendation, organization_id, store_id, "status", "approved"),
                    "recommendations_rejected": self.status_count(PriceRecommendation, organization_id, store_id, "status", "rejected"),
                    "blocked_unsafe_recommendations": self.status_count(PriceRecommendation, organization_id, store_id, "validation_status", "blocked"),
                }
            },
        }

    def get_workflow_metrics(self, user_context: dict, store_id: UUID, *, date_from=None, date_to=None) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.ANALYTICS_READ, Permission.WORKFLOWS_READ, Permission.WORKFLOWS_MANAGE])
        start_at, end_at = self.resolve_range(date_from, date_to)
        return {
            "range": {"date_from": start_at.isoformat(), "date_to": end_at.isoformat()},
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": {
                "workflows": {
                    "workflow_definition_count": self.workflow_definition_count(organization_id, store_id),
                    "enabled_workflow_definition_count": self.workflow_definition_count(organization_id, store_id, is_active=True),
                    "workflow_runs_total": self.scalar_count(WorkflowRun, organization_id, store_id, start_at, end_at),
                    "workflow_runs_failed": self.scalar_count(
                        WorkflowRun,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(WorkflowRun.status == "failed",),
                    ),
                }
            },
        }

    def get_notification_metrics(self, user_context: dict, store_id: UUID, *, date_from=None, date_to=None) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.ANALYTICS_READ, Permission.NOTIFICATIONS_READ, Permission.NOTIFICATIONS_MANAGE])
        start_at, end_at = self.resolve_range(date_from, date_to)
        return {
            "range": {"date_from": start_at.isoformat(), "date_to": end_at.isoformat()},
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": {
                "notifications": {
                    "configured_channels": self.scalar_count(NotificationChannel, organization_id, store_id, start_at, end_at),
                    "deliveries_total": self.scalar_count(NotificationDelivery, organization_id, store_id, start_at, end_at),
                    "deliveries_sent": self.scalar_count(
                        NotificationDelivery,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(NotificationDelivery.status == "sent",),
                    ),
                    "deliveries_failed": self.scalar_count(
                        NotificationDelivery,
                        organization_id,
                        store_id,
                        start_at,
                        end_at,
                        extra_filters=(NotificationDelivery.status == "failed",),
                    ),
                }
            },
        }

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

    def scalar_sum_int(self, column, model, organization_id: UUID, store_id: UUID, start_at: datetime, end_at: datetime, *, extra_filters=()) -> int:
        query = select(func.coalesce(func.sum(column), 0)).select_from(model).where(
            model.organization_id == organization_id,
            model.store_id == store_id,
            model.created_at >= start_at,
            model.created_at <= end_at,
            *extra_filters,
        )
        return int(self.db.scalar(query) or 0)

    def status_count(self, model, organization_id: UUID, store_id: UUID, field_name: str, value: str) -> int:
        column = getattr(model, field_name)
        query = select(func.count()).select_from(model).where(
            model.organization_id == organization_id,
            model.store_id == store_id,
            column == value,
        )
        return int(self.db.scalar(query) or 0)

    def pending_retry_count(self, organization_id: UUID, store_id: UUID) -> int:
        models = (SyncRun, WorkflowRun, ApprovalRequest, NotificationDelivery)
        total = 0
        for model in models:
            total += int(
                self.db.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(
                        model.organization_id == organization_id,
                        model.store_id == store_id,
                        model.next_retry_at.is_not(None),
                    )
                )
                or 0
            )
        return total

    def terminal_failure_count(self, organization_id: UUID, store_id: UUID) -> int:
        models = (SyncRun, WorkflowRun, AgentRun, ApprovalRequest, NotificationDelivery)
        total = 0
        for model in models:
            total += int(
                self.db.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(
                        model.organization_id == organization_id,
                        model.store_id == store_id,
                        model.terminal_failed_at.is_not(None),
                    )
                )
                or 0
            )
        return total

    def requires_operator_count(self, organization_id: UUID, store_id: UUID) -> int:
        models = (SyncRun, WorkflowRun, AgentRun, ApprovalRequest, NotificationDelivery)
        total = 0
        for model in models:
            total += int(
                self.db.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(
                        model.organization_id == organization_id,
                        model.store_id == store_id,
                        model.failure_class == "requires_operator",
                    )
                )
                or 0
            )
        return total

    def average_queue_lag_seconds(self, model, organization_id: UUID, store_id: UUID, start_at: datetime, end_at: datetime) -> int:
        rows = self.db.execute(
            select(model.created_at, model.started_at)
            .where(
                model.organization_id == organization_id,
                model.store_id == store_id,
                model.created_at >= start_at,
                model.created_at <= end_at,
            )
        ).all()
        lags = []
        for created_at, started_at in rows:
            if created_at is None:
                continue
            effective_start = started_at or datetime.now(UTC)
            lags.append(max(int((effective_start - created_at).total_seconds()), 0))
        if not lags:
            return 0
        return int(sum(lags) / len(lags))

    def average_runtime_seconds(self, model, organization_id: UUID, store_id: UUID, start_at: datetime, end_at: datetime) -> int:
        rows = self.db.execute(
            select(model.started_at, model.completed_at)
            .where(
                model.organization_id == organization_id,
                model.store_id == store_id,
                model.created_at >= start_at,
                model.created_at <= end_at,
            )
        ).all()
        durations = []
        for started_at_value, completed_at_value in rows:
            if started_at_value is None or completed_at_value is None:
                continue
            durations.append(max(int((completed_at_value - started_at_value).total_seconds()), 0))
        if not durations:
            return 0
        return int(sum(durations) / len(durations))

    def average_notification_delivery_latency_seconds(self, organization_id: UUID, store_id: UUID, start_at: datetime, end_at: datetime) -> int:
        rows = self.db.execute(
            select(NotificationDelivery.queued_at, NotificationDelivery.sent_at, NotificationDelivery.last_attempted_at)
            .where(
                NotificationDelivery.organization_id == organization_id,
                NotificationDelivery.store_id == store_id,
                NotificationDelivery.created_at >= start_at,
                NotificationDelivery.created_at <= end_at,
            )
        ).all()
        durations = []
        for queued_at, sent_at, last_attempted_at in rows:
            if queued_at is None:
                continue
            completed_at = sent_at or last_attempted_at
            if completed_at is None:
                continue
            durations.append(max(int((completed_at - queued_at).total_seconds()), 0))
        if not durations:
            return 0
        return int(sum(durations) / len(durations))

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

    def workflow_definition_count(self, organization_id: UUID, store_id: UUID, *, is_active: bool | None = None) -> int:
        query = select(func.count()).select_from(Workflow).where(
            Workflow.organization_id == organization_id,
            Workflow.store_id == store_id,
            Workflow.is_system_defined.is_(False),
        )
        if is_active is not None:
            query = query.where(Workflow.is_active.is_(is_active))
        return int(self.db.scalar(query) or 0)

    def require_store_access(self, user_context: dict, store_id: UUID) -> UUID:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        organization_id = UUID(organization["id"])
        store = self.store_repository.get_store(organization_id, store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return organization_id
