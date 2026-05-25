from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.agents.product_content.runner import ProductContentAgentRunner
from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workflow_repository import WorkflowRepository


class CatalogModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.sync_repository = SyncRepository(db)
        self.catalog_repository = CatalogRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.approval_repository = ApprovalRepository(db)
        self.user_repository = UserRepository(db)
        self.agent_runner = ProductContentAgentRunner(db)

    def list_products(self, user_context: dict, store_id: UUID) -> list[dict]:
        require_permission(user_context, Permission.CATALOG_READ)
        store = self._require_store(user_context, store_id)
        products = self.sync_repository.list_products(store.organization_id, store.id)
        return [
            self._serialize_product(
                product,
                variants=self.sync_repository.list_variants(store.organization_id, store.id, product.id),
            )
            for product in products
        ]

    def get_product(self, user_context: dict, store_id: UUID, product_id: UUID) -> dict:
        require_permission(user_context, Permission.CATALOG_READ)
        store = self._require_store(user_context, store_id)
        product = self.sync_repository.get_product(store.organization_id, store.id, product_id)
        if product is None:
            raise AppError(code="not_found", message="Product not found", status_code=404)
        drafts = self.catalog_repository.list_drafts(store.organization_id, store.id, product.id)
        variants = self.sync_repository.list_variants(store.organization_id, store.id, product.id)
        payload = self._serialize_product(product, variants=variants)
        payload["variants"] = [self._serialize_variant(variant) for variant in variants]
        payload["latest_draft"] = self._serialize_draft(drafts[0]) if drafts else None
        return payload

    def list_drafts(self, user_context: dict, store_id: UUID, product_id: UUID) -> list[dict]:
        require_permission(user_context, Permission.CATALOG_READ)
        store = self._require_store(user_context, store_id)
        product = self.sync_repository.get_product(store.organization_id, store.id, product_id)
        if product is None:
            raise AppError(code="not_found", message="Product not found", status_code=404)
        return [self._serialize_draft(draft) for draft in self.catalog_repository.list_drafts(store.organization_id, store.id, product.id)]

    def generate_draft(self, user_context: dict, store_id: UUID, product_id: UUID, payload) -> dict:
        require_permission(user_context, Permission.CATALOG_DRAFT_GENERATE)
        store = self._require_store(user_context, store_id)
        product = self.sync_repository.get_product(store.organization_id, store.id, product_id)
        if product is None:
            raise AppError(code="not_found", message="Product not found", status_code=404)
        result = self.agent_runner.start_generation(
            organization_id=store.organization_id,
            store_id=store.id,
            user_id=UUID(user_context["user"]["id"]),
            product=product,
            generation_targets=payload.generation_targets,
            tone=payload.tone,
            constraints=payload.constraints,
        )
        result["_enqueue_generation"] = True
        self.db.commit()
        return result

    def get_draft(self, user_context: dict, store_id: UUID, product_id: UUID, draft_id: UUID) -> dict:
        require_permission(user_context, Permission.CATALOG_READ)
        store = self._require_store(user_context, store_id)
        draft = self.catalog_repository.get_draft(store.organization_id, store.id, product_id, draft_id)
        if draft is None:
            raise AppError(code="not_found", message="Draft not found", status_code=404)
        return self._serialize_draft(draft)

    def update_draft(self, user_context: dict, store_id: UUID, product_id: UUID, draft_id: UUID, payload) -> dict:
        require_permission(user_context, Permission.CATALOG_DRAFT_EDIT)
        store = self._require_store(user_context, store_id)
        draft = self.catalog_repository.get_draft(store.organization_id, store.id, product_id, draft_id)
        if draft is None:
            raise AppError(code="not_found", message="Draft not found", status_code=404)
        updates = payload.model_dump(exclude_none=True)
        draft = self.catalog_repository.update_draft(draft, **updates)
        self.db.commit()
        return self._serialize_draft(draft)

    def submit_draft_for_approval(self, user_context: dict, store_id: UUID, product_id: UUID, draft_id: UUID, reason: str, idempotency_key: str | None) -> dict:
        require_permission(user_context, Permission.CATALOG_DRAFT_SUBMIT)
        if not idempotency_key:
            raise AppError(code="validation_error", message="Idempotency-Key header is required", status_code=422)
        store = self._require_store(user_context, store_id)
        draft = self.catalog_repository.get_draft(store.organization_id, store.id, product_id, draft_id)
        if draft is None:
            raise AppError(code="not_found", message="Draft not found", status_code=404)
        if draft.status not in {"draft", "rejected"}:
            raise AppError(code="conflict", message="Draft cannot be submitted for approval in its current state", status_code=409)
        approval_request = self.catalog_repository.create_approval_request(
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
            source_snapshot_hash=f"draft:{draft.id}:{draft.updated_at.timestamp()}",
            source_snapshot_created_at=draft.updated_at,
            reasoning=reason,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            idempotency_key=idempotency_key,
            requested_by_user_id=UUID(user_context["user"]["id"]),
        )
        draft = self.catalog_repository.update_draft(
            draft,
            status="submitted_for_approval",
            submitted_approval_request_id=approval_request.id,
        )
        self.workflow_repository.create_audit_event(
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
            for user in self.user_repository.list_users_with_any_role(store.organization_id, ["Owner", "Admin", "Manager"])
            if user.id != UUID(user_context["user"]["id"])
        }
        for reviewer_id in reviewer_ids:
            self.workflow_repository.create_notification(
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
        self.db.commit()
        return {
            "approval_id": str(approval_request.id),
            "approval_status": approval_request.status,
            "draft_status": draft.status,
        }

    def list_orders(self, user_context: dict, store_id: UUID) -> list[dict]:
        require_permission(user_context, Permission.SYNC_READ)
        store = self._require_store(user_context, store_id)
        orders = self.sync_repository.list_orders(store.organization_id, store.id)
        return [
            {
                "id": str(order.id),
                "external_order_id": order.external_order_id,
                "status": order.status,
                "payment_status": order.payment_status,
                "fulfillment_status": order.fulfillment_status,
                "total": str(order.total),
                "currency": order.currency,
                "created_at": order.created_at.isoformat(),
            }
            for order in orders
        ]

    def get_order(self, user_context: dict, store_id: UUID, order_id: UUID) -> dict:
        require_permission(user_context, Permission.SYNC_READ)
        store = self._require_store(user_context, store_id)
        order = self.sync_repository.get_order(store.organization_id, store.id, order_id)
        if order is None:
            raise AppError(code="not_found", message="Order not found", status_code=404)
        return {
            "id": str(order.id),
            "external_order_id": order.external_order_id,
            "status": order.status,
            "payment_status": order.payment_status,
            "fulfillment_status": order.fulfillment_status,
            "total": str(order.total),
            "currency": order.currency,
            "created_at": order.created_at.isoformat(),
        }

    def list_customers(self, user_context: dict, store_id: UUID) -> list[dict]:
        require_permission(user_context, Permission.SYNC_READ)
        store = self._require_store(user_context, store_id)
        customers = self.sync_repository.list_customers(store.organization_id, store.id)
        return [
            {
                "id": str(customer.id),
                "email": customer.email,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "total_orders": customer.total_orders,
                "created_at": customer.created_at.isoformat(),
            }
            for customer in customers
        ]

    def get_customer(self, user_context: dict, store_id: UUID, customer_id: UUID) -> dict:
        require_permission(user_context, Permission.SYNC_READ)
        store = self._require_store(user_context, store_id)
        customer = self.sync_repository.get_customer(store.organization_id, store.id, customer_id)
        if customer is None:
            raise AppError(code="not_found", message="Customer not found", status_code=404)
        return {
            "id": str(customer.id),
            "email": customer.email,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "total_orders": customer.total_orders,
            "created_at": customer.created_at.isoformat(),
        }

    def _require_store(self, user_context: dict, store_id: UUID):
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        store = self.store_repository.get_store(UUID(organization["id"]), store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return store

    @staticmethod
    def _serialize_product(product, *, variants: list | None = None) -> dict:
        inventory_total = sum(variant.inventory_quantity for variant in variants or [])
        return {
            "id": str(product.id),
            "title": product.title,
            "handle": product.handle,
            "vendor": product.vendor,
            "status": product.status,
            "seo_title": product.seo_title,
            "inventory_total": inventory_total,
            "updated_at": product.updated_at.isoformat(),
        }

    @staticmethod
    def _serialize_variant(variant) -> dict:
        return {
            "id": str(variant.id),
            "external_variant_id": variant.external_variant_id,
            "sku": variant.sku,
            "title": variant.title,
            "price": str(variant.price),
            "compare_at_price": str(variant.compare_at_price) if variant.compare_at_price is not None else None,
            "inventory_quantity": variant.inventory_quantity,
        }

    @staticmethod
    def _serialize_draft(draft) -> dict:
        return {
            "id": str(draft.id),
            "product_id": str(draft.product_id),
            "generated_title": draft.generated_title,
            "generated_description": draft.generated_description,
            "generated_tags": draft.generated_tags,
            "generated_seo_title": draft.generated_seo_title,
            "generated_seo_description": draft.generated_seo_description,
            "model_name": draft.model_name,
            "status": draft.status,
            "created_at": draft.created_at.isoformat(),
            "updated_at": draft.updated_at.isoformat(),
        }
