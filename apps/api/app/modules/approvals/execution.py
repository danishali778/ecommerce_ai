from datetime import datetime, timezone
from uuid import UUID

from app.core.errors import AppError
from app.core.redaction import redact_text

from .serializers import serialize_approval
from .snapshots import snapshot_hash


def execute_approval(module, approval_id: str, trace_id: str | None = None) -> dict | None:
    approval = module.db.get(module.approval_model, UUID(approval_id))
    if approval is None or approval.status == "executed":
        return None
    if approval.status != "approved":
        raise AppError(code="conflict", message="Approval is not ready for execution", status_code=409)
    if approval.action_type == "pricing_recommendation_approval":
        recommendation = module.db.get(module.pricing_module._recommendation_model(), approval.entity_id)
        if recommendation is None:
            raise AppError(code="not_found", message="Pricing recommendation not found", status_code=404)
        module.pricing_module.mark_recommendation_approved(recommendation.id)
        module.repository.update_approval(
            approval,
            status="executed",
            execution_status="succeeded",
            execution_error=None,
            trace_id=trace_id or approval.trace_id,
            last_execution_attempt_at=datetime.now(timezone.utc),
        )
        module.workflow_repository.create_audit_event(
            organization_id=approval.organization_id,
            store_id=approval.store_id,
            user_id=approval.reviewed_by_user_id,
            entity_type="approval_request",
            entity_id=approval.id,
            action_type="pricing_approved",
            source_type="celery",
            outcome="executed",
            metadata_json={"recommendation_id": str(recommendation.id), "published_to_store": False},
        )
        module.db.commit()
        return serialize_approval(approval)
    draft = module.require_publishable_draft(approval)
    reviewer_id = approval.reviewed_by_user_id
    if snapshot_hash(draft) != approval.source_snapshot_hash:
        module.repository.update_approval(
            approval,
            status="cancelled",
            execution_status="cancelled",
            execution_error="Source snapshot changed before execution",
            trace_id=trace_id or approval.trace_id,
            last_execution_attempt_at=datetime.now(timezone.utc),
        )
        if draft.status != "published":
            module.catalog_repository.update_draft(draft, status="draft", submitted_approval_request_id=None)
        module.workflow_repository.create_audit_event(
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
        module.db.commit()
        return serialize_approval(approval)
    store = module.store_repository.get_store(approval.organization_id, approval.store_id)
    integration = module.store_repository.get_integration(approval.store_id)
    access_token = module.secret_store.get(integration.secret_reference) if integration and integration.secret_reference else None
    product = module.sync_repository.get_product(approval.organization_id, approval.store_id, draft.product_id)
    if store is None or integration is None or not access_token or product is None:
        raise AppError(code="conflict", message="Approval execution context is incomplete", status_code=409)
    try:
        published = module.shopify_client.publish_product_content(
            store.domain,
            access_token,
            product.external_product_id,
            approval.proposed_action_json,
        )
    except Exception as exc:  # noqa: BLE001
        message = redact_text(str(exc))
        module.repository.update_approval(
            approval,
            status="execution_failed",
            execution_status="failed",
            execution_error=message,
            trace_id=trace_id or approval.trace_id,
            last_execution_attempt_at=datetime.now(timezone.utc),
            retry_count=approval.retry_count + 1,
        )
        for user_id in {approval.requested_by_user_id, reviewer_id} - {None}:
            module.workflow_repository.create_notification(
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
        module.workflow_repository.create_audit_event(
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
        module.db.commit()
        raise
    module.repository.update_approval(
        approval,
        status="executed",
        execution_status="succeeded",
        execution_error=None,
        trace_id=trace_id or approval.trace_id,
        last_execution_attempt_at=datetime.now(timezone.utc),
    )
    module.catalog_repository.update_draft(
        draft,
        status="published",
        published_at=datetime.now(timezone.utc),
    )
    module.workflow_repository.create_audit_event(
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
    module.db.commit()
    return serialize_approval(approval)

