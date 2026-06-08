from __future__ import annotations

from uuid import UUID

from app.core.errors import AppError
from app.core.secret_store import get_secret_store
from app.integrations.shopify import ShopifyClient
from app.modules.pricing import PricingModule
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.models import ApprovalRequest, ProductContentDraft
from app.repositories.store_repository import StoreRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.workflow_repository import WorkflowRepository

from .decisions import approve, cancel, get_approval, list_approvals, reject, retry_execution
from .execution import execute_approval


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
        self.pricing_module = PricingModule(db)
        self.approval_model = ApprovalRequest

    def list_approvals(self, user_context: dict) -> list[dict]:
        return list_approvals(self, user_context)

    def get_approval(self, user_context: dict, approval_id: UUID) -> dict:
        return get_approval(self, user_context, approval_id)

    def approve(self, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None, trace_id: str | None = None) -> dict:
        return approve(self, user_context, approval_id, review_notes, idempotency_key, trace_id=trace_id)

    def reject(self, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None) -> dict:
        return reject(self, user_context, approval_id, review_notes, idempotency_key)

    def cancel(self, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None) -> dict:
        return cancel(self, user_context, approval_id, review_notes, idempotency_key)

    def retry_execution(self, user_context: dict, approval_id: UUID, review_notes: str | None, idempotency_key: str | None, trace_id: str | None = None) -> dict:
        return retry_execution(self, user_context, approval_id, review_notes, idempotency_key, trace_id=trace_id)

    def execute_approval(self, approval_id: str, trace_id: str | None = None) -> dict | None:
        return execute_approval(self, approval_id, trace_id=trace_id)

    def require_publishable_draft(self, approval: ApprovalRequest) -> ProductContentDraft:
        if approval.action_type != "product_content_publish":
            raise AppError(code="approval_not_allowed", message="Approval does not target a publishable product draft", status_code=403)
        draft = self.db.get(ProductContentDraft, approval.entity_id)
        if draft is None:
            raise AppError(code="not_found", message="Draft for approval not found", status_code=404)
        return draft

    def require_approval(self, user_context: dict, approval_id: UUID) -> ApprovalRequest:
        organization = self.require_org(user_context)
        approval = self.repository.get_approval(UUID(organization["id"]), approval_id)
        if approval is None:
            raise AppError(code="not_found", message="Approval not found", status_code=404)
        return approval

    @staticmethod
    def require_org(user_context: dict) -> dict:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        return organization
