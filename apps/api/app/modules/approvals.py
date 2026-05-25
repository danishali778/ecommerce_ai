from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.idempotency import resolve_idempotent_response
from app.core.permissions import Permission
from app.core.redaction import redact_text
from app.core.secret_store import get_secret_store
from app.integrations.shopify import ShopifyClient
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.models import ApprovalRequest, ProductContentDraft
from app.repositories.store_repository import StoreRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.workflow_repository import WorkflowRepository


class ApprovalModule:
    def __init__(self, db) -> None:
        self.db = db
        self.repository = ApprovalRepository(db)
        self.catalog_repository = CatalogRepository(db)
        self.store_repository = StoreRepository(db)
        self.sync_repository = SyncRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.idempotency_repository = IdempotencyRepository(db)
        self.secret_store = get_secret_store()
        self.shopify_client = ShopifyClient()

    def list_approvals(self, user_context: dict) -> list[dict]:
        require_permission(user_context, Permission.APPROVALS_READ)
        organization = self._require_org(user_context)
        approvals = self.repository.list_approvals(UUID(organization["id"]))
        return [self._serialize_approval(approval) for approval in approvals]

    def get_approval(self, user_context: dict, approval_id: UUID) -> dict:
        require_permission(user_context, Permission.APPROVALS_READ)
        approval = self._require_approval(user_context, approval_id)
        return self._serialize_approval(approval)

    def approve(self, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None) -> dict:
        require_permission(user_context, Permission.APPROVALS_REVIEW)
        approval = self._require_approval(user_context, approval_id)
        existing_response, _, fingerprint = resolve_idempotent_response(
            self.idempotency_repository,
            organization_id=approval.organization_id,
            scope=f"approval:approve:{approval.id}",
            idempotency_key=idempotency_key,
            payload={"review_notes": review_notes},
        )
        if existing_response is not None:
            return existing_response
        if approval.status != "pending":
            raise AppError(code="approval_terminal_state", message="Approval is not pending", status_code=409)
        draft = self._require_publishable_draft(approval)
        if self._snapshot_hash(draft) != approval.source_snapshot_hash:
            approval = self._cancel_stale_approval(approval, user_context, review_notes)
            self.db.commit()
            raise AppError(
                code="source_snapshot_changed",
                message="Draft changed after approval request creation",
                status_code=409,
                details={"approval_status": approval.status, "execution_error": approval.execution_error},
            )
        self.repository.update_approval(
            approval,
            status="approved",
            execution_status="queued",
            execution_error=None,
            reviewed_by_user_id=UUID(user_context["user"]["id"]),
            reviewed_at=datetime.now(timezone.utc),
            review_notes=review_notes,
        )
        self.workflow_repository.create_audit_event(
            organization_id=approval.organization_id,
            store_id=approval.store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="approval_request",
            entity_id=approval.id,
            action_type="approve",
            source_type="api",
            outcome="queued",
            metadata_json={"draft_id": str(draft.id)},
        )
        response = self._serialize_approval(approval)
        response["_enqueue_publish"] = True
        self.idempotency_repository.create_record(
            organization_id=approval.organization_id,
            scope=f"approval:approve:{approval.id}",
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            resource_type="approval_request",
            resource_id=approval.id,
            response_json={k: v for k, v in response.items() if not k.startswith("_")},
        )
        self.db.commit()
        return response

    def reject(self, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None) -> dict:
        require_permission(user_context, Permission.APPROVALS_REVIEW)
        approval = self._require_approval(user_context, approval_id)
        existing_response, _, fingerprint = resolve_idempotent_response(
            self.idempotency_repository,
            organization_id=approval.organization_id,
            scope=f"approval:reject:{approval.id}",
            idempotency_key=idempotency_key,
            payload={"review_notes": review_notes},
        )
        if existing_response is not None:
            return existing_response
        if approval.status != "pending":
            raise AppError(code="approval_terminal_state", message="Approval is not pending", status_code=409)
        self.repository.update_approval(
            approval,
            status="rejected",
            execution_status=None,
            reviewed_by_user_id=UUID(user_context["user"]["id"]),
            reviewed_at=datetime.now(timezone.utc),
            review_notes=review_notes,
        )
        draft = self.db.get(ProductContentDraft, approval.entity_id)
        if draft is not None:
            self.catalog_repository.update_draft(draft, status="rejected")
        self.workflow_repository.create_audit_event(
            organization_id=approval.organization_id,
            store_id=approval.store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="approval_request",
            entity_id=approval.id,
            action_type="reject",
            source_type="api",
            outcome="rejected",
            metadata_json={},
        )
        response = self._serialize_approval(approval)
        self.idempotency_repository.create_record(
            organization_id=approval.organization_id,
            scope=f"approval:reject:{approval.id}",
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            resource_type="approval_request",
            resource_id=approval.id,
            response_json=response,
        )
        self.db.commit()
        return response

    def cancel(self, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None) -> dict:
        require_permission(user_context, Permission.APPROVALS_CANCEL)
        approval = self._require_approval(user_context, approval_id)
        existing_response, _, fingerprint = resolve_idempotent_response(
            self.idempotency_repository,
            organization_id=approval.organization_id,
            scope=f"approval:cancel:{approval.id}",
            idempotency_key=idempotency_key,
            payload={"review_notes": review_notes},
        )
        if existing_response is not None:
            return existing_response
        if approval.status not in {"pending", "approved", "execution_failed"}:
            raise AppError(code="approval_terminal_state", message="Approval cannot be cancelled", status_code=409)
        self.repository.update_approval(
            approval,
            status="cancelled",
            execution_status="cancelled",
            execution_error=review_notes or "Approval cancelled",
            reviewed_by_user_id=UUID(user_context["user"]["id"]),
            reviewed_at=datetime.now(timezone.utc),
            review_notes=review_notes,
        )
        draft = self.db.get(ProductContentDraft, approval.entity_id)
        if draft is not None and draft.status != "published":
            self.catalog_repository.update_draft(draft, status="draft", submitted_approval_request_id=None)
        self.workflow_repository.create_audit_event(
            organization_id=approval.organization_id,
            store_id=approval.store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="approval_request",
            entity_id=approval.id,
            action_type="cancel",
            source_type="api",
            outcome="cancelled",
            metadata_json={},
        )
        response = self._serialize_approval(approval)
        self.idempotency_repository.create_record(
            organization_id=approval.organization_id,
            scope=f"approval:cancel:{approval.id}",
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            resource_type="approval_request",
            resource_id=approval.id,
            response_json=response,
        )
        self.db.commit()
        return response

    def retry_execution(self, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None) -> dict:
        require_permission(user_context, Permission.APPROVALS_RETRY_EXECUTION)
        approval = self._require_approval(user_context, approval_id)
        existing_response, _, fingerprint = resolve_idempotent_response(
            self.idempotency_repository,
            organization_id=approval.organization_id,
            scope=f"approval:retry_execution:{approval.id}",
            idempotency_key=idempotency_key,
            payload={"review_notes": review_notes},
        )
        if existing_response is not None:
            return existing_response
        if approval.status != "execution_failed":
            raise AppError(code="conflict", message="Only failed executions can be retried", status_code=409)
        draft = self._require_publishable_draft(approval)
        self.repository.update_approval(
            approval,
            status="approved",
            execution_status="queued",
            execution_error=None,
            reviewed_by_user_id=UUID(user_context["user"]["id"]),
            reviewed_at=datetime.now(timezone.utc),
            review_notes=review_notes,
        )
        if draft.status != "published":
            self.catalog_repository.update_draft(draft, status="submitted_for_approval")
        self.workflow_repository.create_audit_event(
            organization_id=approval.organization_id,
            store_id=approval.store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="approval_request",
            entity_id=approval.id,
            action_type="retry_execution",
            source_type="api",
            outcome="queued",
            metadata_json={},
        )
        response = self._serialize_approval(approval)
        response["_enqueue_publish"] = True
        self.idempotency_repository.create_record(
            organization_id=approval.organization_id,
            scope=f"approval:retry_execution:{approval.id}",
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            resource_type="approval_request",
            resource_id=approval.id,
            response_json={k: v for k, v in response.items() if not k.startswith("_")},
        )
        self.db.commit()
        return response

    def execute_approval(self, approval_id: str) -> dict | None:
        approval = self.db.get(ApprovalRequest, UUID(approval_id))
        if approval is None or approval.status == "executed":
            return None
        if approval.status != "approved":
            raise AppError(code="conflict", message="Approval is not ready for execution", status_code=409)
        draft = self._require_publishable_draft(approval)
        reviewer_id = approval.reviewed_by_user_id
        if self._snapshot_hash(draft) != approval.source_snapshot_hash:
            self.repository.update_approval(
                approval,
                status="cancelled",
                execution_status="cancelled",
                execution_error="Source snapshot changed before execution",
                last_execution_attempt_at=datetime.now(timezone.utc),
            )
            if draft.status != "published":
                self.catalog_repository.update_draft(draft, status="draft", submitted_approval_request_id=None)
            self.workflow_repository.create_audit_event(
                organization_id=approval.organization_id,
                store_id=approval.store_id,
                user_id=reviewer_id,
                entity_type="approval_request",
                entity_id=approval.id,
                action_type="cancel_stale",
                source_type="celery",
                outcome="cancelled",
                metadata_json={"reason": "source_snapshot_changed"},
            )
            self.db.commit()
            return self._serialize_approval(approval)
        store = self.store_repository.get_store(approval.organization_id, approval.store_id)
        integration = self.store_repository.get_integration(approval.store_id)
        access_token = self.secret_store.get(integration.secret_reference) if integration and integration.secret_reference else None
        product = self.sync_repository.get_product(approval.organization_id, approval.store_id, draft.product_id)
        if store is None or integration is None or not access_token or product is None:
            raise AppError(code="conflict", message="Approval execution context is incomplete", status_code=409)
        try:
            published = self.shopify_client.publish_product_content(
                store.domain,
                access_token,
                product.external_product_id,
                approval.proposed_action_json,
            )
        except Exception as exc:  # noqa: BLE001
            message = redact_text(str(exc))
            self.repository.update_approval(
                approval,
                status="execution_failed",
                execution_status="failed",
                execution_error=message,
                last_execution_attempt_at=datetime.now(timezone.utc),
                retry_count=approval.retry_count + 1,
            )
            for user_id in {approval.requested_by_user_id, reviewer_id} - {None}:
                self.workflow_repository.create_notification(
                    organization_id=approval.organization_id,
                    store_id=approval.store_id,
                    user_id=user_id,
                    type="publish_failed",
                    channel="in_app",
                    title="Product publish failed",
                    body=message,
                    payload_json={"approval_id": str(approval.id)},
                    status="unread",
                )
            self.workflow_repository.create_audit_event(
                organization_id=approval.organization_id,
                store_id=approval.store_id,
                user_id=reviewer_id,
                entity_type="approval_request",
                entity_id=approval.id,
                action_type="publish_failed",
                source_type="celery",
                outcome="failed",
                metadata_json={"error": message},
            )
            self.db.commit()
            raise
        self.repository.update_approval(
            approval,
            status="executed",
            execution_status="succeeded",
            execution_error=None,
            last_execution_attempt_at=datetime.now(timezone.utc),
        )
        self.catalog_repository.update_draft(
            draft,
            status="published",
            published_at=datetime.now(timezone.utc),
        )
        self.workflow_repository.create_audit_event(
            organization_id=approval.organization_id,
            store_id=approval.store_id,
            user_id=reviewer_id,
            entity_type="approval_request",
            entity_id=approval.id,
            action_type="publish_executed",
            source_type="celery",
            outcome="executed",
            metadata_json={"published_product_id": published["id"]},
        )
        self.db.commit()
        return self._serialize_approval(approval)

    def _cancel_stale_approval(self, approval: ApprovalRequest, user_context: dict, review_notes: str | None) -> ApprovalRequest:
        draft = self.db.get(ProductContentDraft, approval.entity_id)
        if draft is not None and draft.status != "published":
            self.catalog_repository.update_draft(draft, status="draft", submitted_approval_request_id=None)
        self.repository.update_approval(
            approval,
            status="cancelled",
            execution_status="cancelled",
            execution_error="Source snapshot changed before execution",
            reviewed_by_user_id=UUID(user_context["user"]["id"]),
            reviewed_at=datetime.now(timezone.utc),
            review_notes=review_notes,
        )
        self.workflow_repository.create_audit_event(
            organization_id=approval.organization_id,
            store_id=approval.store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="approval_request",
            entity_id=approval.id,
            action_type="cancel_stale",
            source_type="api",
            outcome="cancelled",
            metadata_json={"reason": "source_snapshot_changed"},
        )
        return approval

    def _require_publishable_draft(self, approval: ApprovalRequest) -> ProductContentDraft:
        if approval.action_type != "product_content_publish":
            raise AppError(code="approval_not_allowed", message="Only product content publish is executable in P0", status_code=403)
        draft = self.db.get(ProductContentDraft, approval.entity_id)
        if draft is None:
            raise AppError(code="not_found", message="Draft for approval not found", status_code=404)
        return draft

    def _require_approval(self, user_context: dict, approval_id: UUID) -> ApprovalRequest:
        organization = self._require_org(user_context)
        approval = self.repository.get_approval(UUID(organization["id"]), approval_id)
        if approval is None:
            raise AppError(code="not_found", message="Approval not found", status_code=404)
        return approval

    @staticmethod
    def _require_org(user_context: dict) -> dict:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        return organization

    @staticmethod
    def _snapshot_hash(draft: ProductContentDraft) -> str:
        return f"draft:{draft.id}:{draft.updated_at.timestamp()}"

    @staticmethod
    def _serialize_approval(approval: ApprovalRequest) -> dict:
        return {
            "id": str(approval.id),
            "status": approval.status,
            "action_type": approval.action_type,
            "entity_type": approval.entity_type,
            "entity_id": str(approval.entity_id),
            "reasoning": approval.reasoning,
            "review_notes": approval.review_notes,
            "execution_status": approval.execution_status,
            "execution_error": approval.execution_error,
            "expires_at": approval.expires_at.isoformat(),
            "created_at": approval.created_at.isoformat(),
            "updated_at": approval.updated_at.isoformat(),
        }
