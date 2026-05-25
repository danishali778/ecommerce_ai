from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission

from .serializers import serialize_draft
from .snapshots import snapshot_hash


def list_drafts(module, user_context: dict, store_id: UUID, product_id: UUID) -> list[dict]:
    require_permission(user_context, Permission.CATALOG_READ)
    store = module.require_store(user_context, store_id)
    product = module.sync_repository.get_product(store.organization_id, store.id, product_id)
    if product is None:
        raise AppError(code="not_found", message="Product not found", status_code=404)
    return [serialize_draft(draft) for draft in module.catalog_repository.list_drafts(store.organization_id, store.id, product.id)]


def generate_draft(module, user_context: dict, store_id: UUID, product_id: UUID, payload) -> dict:
    require_permission(user_context, Permission.CATALOG_DRAFT_GENERATE)
    store = module.require_store(user_context, store_id)
    product = module.sync_repository.get_product(store.organization_id, store.id, product_id)
    if product is None:
        raise AppError(code="not_found", message="Product not found", status_code=404)
    result = module.agent_runner.start_generation(
        organization_id=store.organization_id,
        store_id=store.id,
        user_id=UUID(user_context["user"]["id"]),
        product=product,
        generation_targets=payload.generation_targets,
        tone=payload.tone,
        constraints=payload.constraints,
    )
    result["_enqueue_generation"] = True
    module.db.commit()
    return result


def get_draft(module, user_context: dict, store_id: UUID, product_id: UUID, draft_id: UUID) -> dict:
    require_permission(user_context, Permission.CATALOG_READ)
    store = module.require_store(user_context, store_id)
    draft = module.catalog_repository.get_draft(store.organization_id, store.id, product_id, draft_id)
    if draft is None:
        raise AppError(code="not_found", message="Draft not found", status_code=404)
    return serialize_draft(draft)


def update_draft(module, user_context: dict, store_id: UUID, product_id: UUID, draft_id: UUID, payload) -> dict:
    require_permission(user_context, Permission.CATALOG_DRAFT_EDIT)
    store = module.require_store(user_context, store_id)
    draft = module.catalog_repository.get_draft(store.organization_id, store.id, product_id, draft_id)
    if draft is None:
        raise AppError(code="not_found", message="Draft not found", status_code=404)
    updates = payload.model_dump(exclude_none=True)
    draft = module.catalog_repository.update_draft(draft, **updates)
    module.db.commit()
    return serialize_draft(draft)


def submit_draft_for_approval(module, user_context: dict, store_id: UUID, product_id: UUID, draft_id: UUID, reason: str, idempotency_key: str | None) -> dict:
    require_permission(user_context, Permission.CATALOG_DRAFT_SUBMIT)
    if not idempotency_key:
        raise AppError(code="validation_error", message="Idempotency-Key header is required", status_code=422)
    store = module.require_store(user_context, store_id)
    draft = module.catalog_repository.get_draft(store.organization_id, store.id, product_id, draft_id)
    if draft is None:
        raise AppError(code="not_found", message="Draft not found", status_code=404)
    if draft.status not in {"draft", "rejected"}:
        raise AppError(code="conflict", message="Draft cannot be submitted for approval in its current state", status_code=409)
    approval_request = module.catalog_repository.create_approval_request(
        organization_id=store.organization_id,
        store_id=store.id,
        action_type="product_content_publish",
        entity_type="product_content_draft",
        entity_id=draft.id,
        workflow_run_id=None,
        agent_run_id=None,
        proposed_action_json={
            "draft_id": str(draft.id),
            "product_id": str(draft.product_id),
            "generated_title": draft.generated_title,
            "generated_description": draft.generated_description,
            "generated_tags": draft.generated_tags,
            "generated_seo_title": draft.generated_seo_title,
            "generated_seo_description": draft.generated_seo_description,
        },
        source_snapshot_hash=snapshot_hash(draft),
        source_snapshot_created_at=draft.updated_at,
        reasoning=reason,
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        idempotency_key=idempotency_key,
        requested_by_user_id=UUID(user_context["user"]["id"]),
    )
    draft = module.catalog_repository.update_draft(
        draft,
        status="submitted_for_approval",
        submitted_approval_request_id=approval_request.id,
    )
    module.workflow_repository.create_audit_event(
        organization_id=store.organization_id,
        store_id=store.id,
        user_id=UUID(user_context["user"]["id"]),
        entity_type="product_content_draft",
        entity_id=draft.id,
        action_type="submit_approval",
        source_type="api",
        outcome="succeeded",
        metadata_json={"approval_id": str(approval_request.id)},
    )
    reviewer_ids = {
        user.id
        for user in module.user_repository.list_users_with_any_role(store.organization_id, ["Owner", "Admin", "Manager"])
        if user.id != UUID(user_context["user"]["id"])
    }
    for reviewer_id in reviewer_ids:
        module.workflow_repository.create_notification(
            organization_id=store.organization_id,
            store_id=store.id,
            user_id=reviewer_id,
            type="approval_pending",
            channel="in_app",
            title="Approval review requested",
            body=f"A product content draft for {draft.product_id} is awaiting approval.",
            payload_json={"approval_id": str(approval_request.id), "draft_id": str(draft.id)},
            status="unread",
        )
    module.db.commit()
    return {
        "approval_id": str(approval_request.id),
        "approval_status": approval_request.status,
        "draft_status": draft.status,
    }

