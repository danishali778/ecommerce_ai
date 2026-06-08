from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.agents.fraud_risk.runner import FraudRiskAgentRunner
from app.core.authz import require_any_permission, require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.repositories.fraud_repository import FraudRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.workflow_repository import WorkflowRepository


def serialize_risk_review(review) -> dict[str, Any]:
    return {
        "id": str(review.id),
        "order_id": str(review.order_id),
        "agent_run_id": str(review.agent_run_id) if review.agent_run_id else None,
        "risk_score": review.risk_score,
        "risk_status": review.risk_status,
        "reason_codes_json": review.reason_codes_json,
        "explanation_json": review.explanation_json,
        "explanation_summary": review.explanation_summary,
        "confidence_score": float(review.confidence_score) if review.confidence_score is not None else None,
        "needs_human_review": review.needs_human_review,
        "review_reason_code": review.review_reason_code,
        "recommended_decision": review.recommended_decision,
        "decision": review.decision,
        "decision_notes": review.decision_notes,
        "reviewed_by_user_id": str(review.reviewed_by_user_id) if review.reviewed_by_user_id else None,
        "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None,
        "created_at": review.created_at.isoformat(),
        "updated_at": review.updated_at.isoformat(),
    }


class FraudModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.sync_repository = SyncRepository(db)
        self.fraud_repository = FraudRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.agent_runner = FraudRiskAgentRunner(db)

    def get_order_risk_score(self, user_context: dict, store_id: UUID, order_id: UUID) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.FRAUD_READ, Permission.FRAUD_REVIEW])
        order = self.sync_repository.get_order(organization_id, store_id, order_id)
        if order is None:
            raise AppError(code="not_found", message="Order not found", status_code=404)
        return {
            "order_id": str(order.id),
            "risk_score": order.risk_score or 0,
            "risk_status": order.risk_status or "low_risk",
        }

    def list_risk_reviews(self, user_context: dict, store_id: UUID, *, risk_status: str | None = None) -> list[dict]:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.FRAUD_READ, Permission.FRAUD_REVIEW])
        return [
            serialize_risk_review(review)
            for review in self.fraud_repository.list_reviews(organization_id, store_id, risk_status=risk_status)
        ]

    def get_risk_review(self, user_context: dict, store_id: UUID, review_id: UUID) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.FRAUD_READ, Permission.FRAUD_REVIEW])
        review = self.fraud_repository.get_review(organization_id, store_id, review_id)
        if review is None:
            raise AppError(code="not_found", message="Risk review not found", status_code=404)
        return serialize_risk_review(review)

    def record_decision(self, user_context: dict, store_id: UUID, review_id: UUID, payload) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.FRAUD_REVIEW)
        review = self.fraud_repository.get_review(organization_id, store_id, review_id)
        if review is None:
            raise AppError(code="not_found", message="Risk review not found", status_code=404)
        decision = payload.decision.lower()
        if decision not in {"approved", "held", "rejected"}:
            raise AppError(code="validation_error", message="Unsupported fraud review decision", status_code=422)
        self.fraud_repository.update_review(
            review,
            decision=decision,
            decision_notes=payload.decision_notes,
            risk_status="reviewed",
            reviewed_by_user_id=UUID(user_context["user"]["id"]),
            reviewed_at=datetime.now(timezone.utc),
        )
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="risk_review",
            entity_id=review.id,
            action_type="decision_recorded",
            source_type="api",
            outcome=decision,
            metadata_json={"decision": decision},
        )
        self.db.commit()
        return serialize_risk_review(review)

    def process_sync_run(self, sync_run) -> dict[str, int]:
        agent_runs_queued = 0
        agent_run_ids: list[str] = []
        for order in self.sync_repository.list_orders_for_sync_run(sync_run.id):
            run_state = self.agent_runner.start_generation(
                organization_id=order.organization_id,
                store_id=order.store_id,
                order=order,
                triggered_by_user_id=sync_run.triggered_by_user_id,
                trace_id=getattr(sync_run, "trace_id", None),
            )
            agent_runs_queued += 1
            agent_run_ids.append(run_state["agent_run_id"])
        self.db.flush()
        return {"orders_risk_assessments_queued": agent_runs_queued, "_agent_run_ids": agent_run_ids}

    def require_store_access(self, user_context: dict, store_id: UUID) -> UUID:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        organization_id = UUID(organization["id"])
        store = self.store_repository.get_store(organization_id, store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return organization_id
