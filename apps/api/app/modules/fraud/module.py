from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

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
        "risk_score": review.risk_score,
        "risk_status": review.risk_status,
        "reason_codes_json": review.reason_codes_json,
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
        reviews_created = 0
        orders_scored = 0
        for order in self.sync_repository.list_orders_for_sync_run(sync_run.id):
            customer = (
                self.sync_repository.get_customer(order.organization_id, order.store_id, order.customer_id)
                if order.customer_id
                else None
            )
            score, status, reasons = self._score_order(order, customer)
            order.risk_score = score
            order.risk_status = status
            orders_scored += 1
            if status == "high_risk":
                review = self.fraud_repository.get_pending_review_for_order(order.id)
                if review is None:
                    self.fraud_repository.create_review(
                        organization_id=order.organization_id,
                        store_id=order.store_id,
                        order_id=order.id,
                        risk_score=score,
                        risk_status="pending_review",
                        reason_codes_json=reasons,
                        decision=None,
                        decision_notes=None,
                    )
                    reviews_created += 1
                    self.workflow_repository.create_audit_event(
                        organization_id=order.organization_id,
                        store_id=order.store_id,
                        user_id=sync_run.triggered_by_user_id,
                        entity_type="risk_review",
                        entity_id=order.id,
                        action_type="created",
                        source_type="sync",
                        outcome="queued",
                        metadata_json={"reasons": reasons, "risk_score": score},
                    )
        self.db.flush()
        return {"orders_scored": orders_scored, "risk_reviews_created": reviews_created}

    def _score_order(self, order, customer) -> tuple[int, str, list[str]]:
        score = 0
        reasons: list[str] = []
        customer_total_orders = self._as_int(customer.total_orders if customer else 0)
        order_total = self._as_decimal(order.total)
        payment_attempt_count = self._as_int(order.payment_attempt_count)
        if order.billing_country and order.shipping_country and order.billing_country != order.shipping_country:
            score += 25
            reasons.append("billing_shipping_country_mismatch")
        if order.billing_postal_code and order.shipping_postal_code and order.billing_postal_code != order.shipping_postal_code:
            score += 20
            reasons.append("billing_shipping_postal_mismatch")
        if customer_total_orders <= 1 and order_total >= Decimal("250"):
            score += 30
            reasons.append("high_value_first_order")
        if payment_attempt_count >= 3:
            score += 15
            reasons.append("elevated_payment_attempt_count")
        if customer and customer_total_orders <= 2 and order_total >= Decimal("150"):
            score += 20
            reasons.append("low_history_high_total")

        if score >= 60:
            return score, "high_risk", reasons
        if score >= 30:
            return score, "medium_risk", reasons
        return score, "low_risk", reasons

    @staticmethod
    def _as_int(value) -> int:
        if value is None:
            return 0
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _as_decimal(value) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value).strip())
        except Exception:  # noqa: BLE001
            return Decimal("0")

    def require_store_access(self, user_context: dict, store_id: UUID) -> UUID:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        organization_id = UUID(organization["id"])
        store = self.store_repository.get_store(organization_id, store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return organization_id
