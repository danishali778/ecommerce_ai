from datetime import datetime, timezone
from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.idempotency import resolve_idempotent_response
from app.core.permissions import Permission
from app.repositories.models import ProductContentDraft

from .serializers import serialize_approval
from .snapshots import snapshot_hash


def list_approvals(module, user_context: dict) -> list[dict]:
    require_permission(user_context, Permission.APPROVALS_READ)
    organization = module.require_org(user_context)
    approvals = module.repository.list_approvals(UUID(organization["id"]))
    return [serialize_approval(approval) for approval in approvals]


def get_approval(module, user_context: dict, approval_id: UUID) -> dict:
    require_permission(user_context, Permission.APPROVALS_READ)
    approval = module.require_approval(user_context, approval_id)
    return serialize_approval(approval)


def approve(module, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None, trace_id: str | None = None) -> dict:
    require_permission(user_context, Permission.APPROVALS_REVIEW)
    approval = module.require_approval(user_context, approval_id)
    existing_response, _, fingerprint = resolve_idempotent_response(
        module.idempotency_repository,
        organization_id=approval.organization_id,
        scope=f"approval:approve:{approval.id}",
        idempotency_key=idempotency_key,
        payload={"review_notes": review_notes},
    )
    if existing_response is not None:
        return existing_response
    if approval.status != "pending":
        raise AppError(code="approval_terminal_state", message="Approval is not pending", status_code=409)
    metadata_json = {}
    if approval.action_type == "product_content_publish":
        draft = module.require_publishable_draft(approval)
        if snapshot_hash(draft) != approval.source_snapshot_hash:
            approval = cancel_stale_approval(module, approval, user_context, review_notes)
            module.db.commit()
            raise AppError(
                code="source_snapshot_changed",
                message="Draft changed after approval request creation",
                status_code=409,
                details={"approval_status": approval.status, "execution_error": approval.execution_error},
            )
        metadata_json = {"draft_id": str(draft.id)}
    elif approval.action_type == "pricing_recommendation_approval":
        recommendation = module.db.get(module.pricing_module._recommendation_model(), approval.entity_id)
        if recommendation is None:
            raise AppError(code="not_found", message="Pricing recommendation not found", status_code=404)
        if recommendation.status == "superseded":
            raise AppError(code="approval_terminal_state", message="Recommendation has been superseded", status_code=409)
        metadata_json = {"recommendation_id": str(approval.entity_id)}
    module.repository.update_approval(
        approval,
        status="approved",
        execution_status="queued",
        execution_error=None,
        trace_id=trace_id or approval.trace_id,
        reviewed_by_user_id=UUID(user_context["user"]["id"]),
        reviewed_at=datetime.now(timezone.utc),
        review_notes=review_notes,
    )
    module.workflow_repository.create_audit_event(
        organization_id=approval.organization_id,
        store_id=approval.store_id,
        user_id=UUID(user_context["user"]["id"]),
        entity_type="approval_request",
        entity_id=approval.id,
        action_type="approve",
        source_type="api",
        outcome="queued",
        metadata_json=metadata_json,
    )
    response = serialize_approval(approval)
    response["_enqueue_execution"] = True
    module.idempotency_repository.create_record(
        organization_id=approval.organization_id,
        scope=f"approval:approve:{approval.id}",
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        resource_type="approval_request",
        resource_id=approval.id,
        response_json={k: v for k, v in response.items() if not k.startswith("_")},
    )
    module.db.commit()
    return response


def reject(module, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None) -> dict:
    require_permission(user_context, Permission.APPROVALS_REVIEW)
    approval = module.require_approval(user_context, approval_id)
    existing_response, _, fingerprint = resolve_idempotent_response(
        module.idempotency_repository,
        organization_id=approval.organization_id,
        scope=f"approval:reject:{approval.id}",
        idempotency_key=idempotency_key,
        payload={"review_notes": review_notes},
    )
    if existing_response is not None:
        return existing_response
    if approval.status != "pending":
        raise AppError(code="approval_terminal_state", message="Approval is not pending", status_code=409)
    module.repository.update_approval(
        approval,
        status="rejected",
        execution_status=None,
        reviewed_by_user_id=UUID(user_context["user"]["id"]),
        reviewed_at=datetime.now(timezone.utc),
        review_notes=review_notes,
    )
    draft = module.db.get(ProductContentDraft, approval.entity_id)
    if draft is not None:
        module.catalog_repository.update_draft(draft, status="rejected")
    elif approval.action_type == "pricing_recommendation_approval":
        module.pricing_module.mark_recommendation_rejected(approval.entity_id)
    module.workflow_repository.create_audit_event(
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
    response = serialize_approval(approval)
    module.idempotency_repository.create_record(
        organization_id=approval.organization_id,
        scope=f"approval:reject:{approval.id}",
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        resource_type="approval_request",
        resource_id=approval.id,
        response_json=response,
    )
    module.db.commit()
    return response


def cancel(module, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None) -> dict:
    require_permission(user_context, Permission.APPROVALS_CANCEL)
    approval = module.require_approval(user_context, approval_id)
    existing_response, _, fingerprint = resolve_idempotent_response(
        module.idempotency_repository,
        organization_id=approval.organization_id,
        scope=f"approval:cancel:{approval.id}",
        idempotency_key=idempotency_key,
        payload={"review_notes": review_notes},
    )
    if existing_response is not None:
        return existing_response
    if approval.status not in {"pending", "approved", "execution_failed"}:
        raise AppError(code="approval_terminal_state", message="Approval cannot be cancelled", status_code=409)
    module.repository.update_approval(
        approval,
        status="cancelled",
        execution_status="cancelled",
        execution_error=review_notes or "Approval cancelled",
        reviewed_by_user_id=UUID(user_context["user"]["id"]),
        reviewed_at=datetime.now(timezone.utc),
        review_notes=review_notes,
    )
    draft = module.db.get(ProductContentDraft, approval.entity_id)
    if draft is not None and draft.status != "published":
        module.catalog_repository.update_draft(draft, status="draft", submitted_approval_request_id=None)
    elif approval.action_type == "pricing_recommendation_approval":
        module.pricing_module.mark_recommendation_rejected(approval.entity_id)
    module.workflow_repository.create_audit_event(
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
    response = serialize_approval(approval)
    module.idempotency_repository.create_record(
        organization_id=approval.organization_id,
        scope=f"approval:cancel:{approval.id}",
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        resource_type="approval_request",
        resource_id=approval.id,
        response_json=response,
    )
    module.db.commit()
    return response


def retry_execution(module, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None, trace_id: str | None = None) -> dict:
    require_permission(user_context, Permission.APPROVALS_RETRY_EXECUTION)
    approval = module.require_approval(user_context, approval_id)
    existing_response, _, fingerprint = resolve_idempotent_response(
        module.idempotency_repository,
        organization_id=approval.organization_id,
        scope=f"approval:retry_execution:{approval.id}",
        idempotency_key=idempotency_key,
        payload={"review_notes": review_notes},
    )
    if existing_response is not None:
        return existing_response
    if approval.status != "execution_failed":
        raise AppError(code="conflict", message="Only failed executions can be retried", status_code=409)
    draft = None
    if approval.action_type == "product_content_publish":
        draft = module.require_publishable_draft(approval)
    module.repository.update_approval(
        approval,
        status="approved",
        execution_status="queued",
        execution_error=None,
        trace_id=trace_id or approval.trace_id,
        reviewed_by_user_id=UUID(user_context["user"]["id"]),
        reviewed_at=datetime.now(timezone.utc),
        review_notes=review_notes,
    )
    if draft is not None and draft.status != "published":
        module.catalog_repository.update_draft(draft, status="submitted_for_approval")
    module.workflow_repository.create_audit_event(
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
    response = serialize_approval(approval)
    response["_enqueue_execution"] = True
    module.idempotency_repository.create_record(
        organization_id=approval.organization_id,
        scope=f"approval:retry_execution:{approval.id}",
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        resource_type="approval_request",
        resource_id=approval.id,
        response_json={k: v for k, v in response.items() if not k.startswith("_")},
    )
    module.db.commit()
    return response


def cancel_stale_approval(module, approval, user_context: dict, review_notes: str | None):
    draft = module.db.get(ProductContentDraft, approval.entity_id)
    if draft is not None and draft.status != "published":
        module.catalog_repository.update_draft(draft, status="draft", submitted_approval_request_id=None)
    module.repository.update_approval(
        approval,
        status="cancelled",
        execution_status="cancelled",
        execution_error="Source snapshot changed before execution",
        reviewed_by_user_id=UUID(user_context["user"]["id"]),
        reviewed_at=datetime.now(timezone.utc),
        review_notes=review_notes,
    )
    module.workflow_repository.create_audit_event(
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

