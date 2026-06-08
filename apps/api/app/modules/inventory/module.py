from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.agents.inventory.runner import InventoryAgentRunner
from app.core.authz import require_any_permission, require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.core.settings import get_settings
from app.modules.workflows.events import emit_workflow_event
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.workflow_repository import WorkflowRepository


def serialize_alert(alert) -> dict[str, Any]:
    return {
        "id": str(alert.id),
        "product_id": str(alert.product_id),
        "variant_id": str(alert.variant_id),
        "threshold_value": alert.threshold_value,
        "current_quantity": alert.current_quantity,
        "status": alert.status,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "created_at": alert.created_at.isoformat(),
        "updated_at": alert.updated_at.isoformat(),
    }


def serialize_suggestion(suggestion, draft=None) -> dict[str, Any]:
    payload = {
        "id": str(suggestion.id),
        "inventory_alert_id": str(suggestion.inventory_alert_id),
        "product_id": str(suggestion.product_id),
        "variant_id": str(suggestion.variant_id) if suggestion.variant_id else None,
        "agent_run_id": str(suggestion.agent_run_id) if suggestion.agent_run_id else None,
        "recommended_quantity": suggestion.recommended_quantity,
        "current_quantity": suggestion.current_quantity,
        "threshold_value": suggestion.threshold_value,
        "rationale_json": suggestion.rationale_json,
        "rationale_summary": suggestion.rationale_summary,
        "urgency": suggestion.urgency,
        "confidence_score": float(suggestion.confidence_score) if suggestion.confidence_score is not None else None,
        "needs_human_review": suggestion.needs_human_review,
        "review_reason_code": suggestion.review_reason_code,
        "status": suggestion.status,
        "created_at": suggestion.created_at.isoformat(),
        "updated_at": suggestion.updated_at.isoformat(),
    }
    if draft is not None:
        payload["supplier_draft"] = {
            "id": str(draft.id),
            "vendor_name": draft.vendor_name,
            "recipient_email": draft.recipient_email,
            "subject": draft.subject,
            "body": draft.body,
            "status": draft.status,
            "created_by_user_id": str(draft.created_by_user_id) if draft.created_by_user_id else None,
            "created_at": draft.created_at.isoformat(),
            "updated_at": draft.updated_at.isoformat(),
        }
    return payload


class InventoryModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.sync_repository = SyncRepository(db)
        self.inventory_repository = InventoryRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.agent_runner = InventoryAgentRunner(db)

    def list_alerts(self, user_context: dict, store_id: UUID, *, status: str | None = None) -> list[dict]:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.INVENTORY_READ, Permission.INVENTORY_MANAGE])
        return [serialize_alert(alert) for alert in self.inventory_repository.list_alerts(organization_id, store_id, status=status)]

    def list_reorder_suggestions(self, user_context: dict, store_id: UUID, *, status: str | None = None) -> list[dict]:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.INVENTORY_READ, Permission.INVENTORY_MANAGE])
        suggestions = self.inventory_repository.list_suggestions(organization_id, store_id, status=status)
        return [
            serialize_suggestion(suggestion, self.inventory_repository.get_draft_for_suggestion(suggestion.id))
            for suggestion in suggestions
        ]

    def get_reorder_suggestion(self, user_context: dict, store_id: UUID, suggestion_id: UUID) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.INVENTORY_READ, Permission.INVENTORY_MANAGE])
        suggestion = self.inventory_repository.get_suggestion(organization_id, store_id, suggestion_id)
        if suggestion is None:
            raise AppError(code="not_found", message="Reorder suggestion not found", status_code=404)
        return serialize_suggestion(suggestion, self.inventory_repository.get_draft_for_suggestion(suggestion.id))

    def create_or_refresh_supplier_draft(self, user_context: dict, store_id: UUID, suggestion_id: UUID, payload) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.INVENTORY_MANAGE)
        suggestion = self.inventory_repository.get_suggestion(organization_id, store_id, suggestion_id)
        if suggestion is None:
            raise AppError(code="not_found", message="Reorder suggestion not found", status_code=404)
        vendor_name = payload.vendor_name or "Supplier"
        subject = payload.subject or f"Reorder request for variant {suggestion.variant_id}"
        body = payload.body or (
            f"Hello {vendor_name},\n\n"
            f"We would like to reorder {suggestion.recommended_quantity} units for variant {suggestion.variant_id}.\n"
            f"Current quantity is {suggestion.current_quantity} and threshold is {suggestion.threshold_value}.\n\n"
            "Please confirm lead time and pricing.\n"
        )
        draft = self.inventory_repository.get_draft_for_suggestion(suggestion.id)
        if draft is None:
            draft = self.inventory_repository.create_draft(
                organization_id=organization_id,
                store_id=store_id,
                reorder_suggestion_id=suggestion.id,
                vendor_name=vendor_name,
                recipient_email=payload.recipient_email,
                subject=subject,
                body=body,
                status="draft",
                created_by_user_id=UUID(user_context["user"]["id"]),
            )
        else:
            self.inventory_repository.update_draft(
                draft,
                vendor_name=vendor_name,
                recipient_email=payload.recipient_email,
                subject=subject,
                body=body,
                status=payload.status or draft.status,
            )
        self.inventory_repository.update_suggestion(suggestion, status="drafted")
        self.db.commit()
        return serialize_suggestion(suggestion, draft)

    def process_sync_run(self, sync_run) -> dict[str, int]:
        threshold = get_settings().low_inventory_threshold
        alerts_created = 0
        suggestions_queued = 0
        agent_run_ids: list[str] = []
        for variant in self.sync_repository.list_variants_for_sync_run(sync_run.id):
            if variant.inventory_quantity >= threshold:
                continue
            alert = self.inventory_repository.get_open_alert_for_variant(sync_run.organization_id, sync_run.store_id, variant.id)
            if alert is None:
                alert = self.inventory_repository.create_alert(
                    organization_id=sync_run.organization_id,
                    store_id=sync_run.store_id,
                    product_id=variant.product_id,
                    variant_id=variant.id,
                    threshold_value=threshold,
                    current_quantity=variant.inventory_quantity,
                    status="open",
                    resolved_at=None,
                )
                alerts_created += 1
                self.workflow_repository.create_audit_event(
                    organization_id=sync_run.organization_id,
                    store_id=sync_run.store_id,
                    user_id=sync_run.triggered_by_user_id,
                    entity_type="inventory_alert",
                    entity_id=alert.id,
                    action_type="created",
                    source_type="sync",
                    outcome="queued",
                    metadata_json={"variant_id": str(variant.id), "inventory_quantity": variant.inventory_quantity},
                )
                emit_workflow_event(
                    organization_id=sync_run.organization_id,
                    store_id=sync_run.store_id,
                    trigger_type="inventory.below_threshold",
                    entity_type="inventory_alert",
                    entity_id=alert.id,
                    payload={
                        "product_id": str(variant.product_id),
                        "variant_id": str(variant.id),
                        "inventory.current_quantity": variant.inventory_quantity,
                        "inventory.threshold_value": threshold,
                        "current_quantity": variant.inventory_quantity,
                        "threshold_value": threshold,
                    },
                )
            else:
                self.inventory_repository.update_alert(alert, current_quantity=variant.inventory_quantity)
            run_state = self.agent_runner.start_generation(
                organization_id=sync_run.organization_id,
                store_id=sync_run.store_id,
                alert=alert,
                triggered_by_user_id=sync_run.triggered_by_user_id,
                trace_id=getattr(sync_run, "trace_id", None),
            )
            suggestions_queued += 1
            agent_run_ids.append(run_state["agent_run_id"])
        self.db.flush()
        return {
            "inventory_alerts_created": alerts_created,
            "reorder_suggestions_queued": suggestions_queued,
            "_agent_run_ids": agent_run_ids,
        }

    def require_store_access(self, user_context: dict, store_id: UUID) -> UUID:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        organization_id = UUID(organization["id"])
        store = self.store_repository.get_store(organization_id, store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return organization_id
