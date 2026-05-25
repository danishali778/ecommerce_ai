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
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.models import Integration, Store, SyncRun
from app.repositories.store_repository import StoreRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workflow_repository import WorkflowRepository


class SyncModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.sync_repository = SyncRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.idempotency_repository = IdempotencyRepository(db)
        self.user_repository = UserRepository(db)
        self.shopify_client = ShopifyClient()
        self.secret_store = get_secret_store()

    def create_sync_run(self, user_context: dict, store_id: UUID, mode: str, idempotency_key: str | None) -> dict:
        require_permission(user_context, Permission.SYNC_TRIGGER)
        store = self._require_store(user_context, store_id)
        existing_response, _, fingerprint = resolve_idempotent_response(
            self.idempotency_repository,
            organization_id=store.organization_id,
            scope="sync:create",
            idempotency_key=idempotency_key,
            payload={"store_id": str(store.id), "mode": mode},
        )
        if existing_response is not None:
            return existing_response
        integration = self.store_repository.get_integration(store.id)
        if integration is None or integration.status != "connected":
            raise AppError(code="conflict", message="Store is not connected to Shopify", status_code=409)
        active = self.sync_repository.get_active_sync_run(store.id)
        if active:
            raise AppError(code="sync_in_progress", message="Another sync is already active", status_code=409)
        sync_run = self.sync_repository.create_sync_run(
            organization_id=store.organization_id,
            store_id=store.id,
            integration_id=integration.id,
            mode=mode,
            status="queued",
            triggered_by_user_id=UUID(user_context["user"]["id"]),
            entity_counts_json={},
            error_details_json={},
        )
        response = self._serialize_sync_run(sync_run)
        response["_enqueue_sync_run"] = True
        self.idempotency_repository.create_record(
            organization_id=store.organization_id,
            scope="sync:create",
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            resource_type="sync_run",
            resource_id=sync_run.id,
            response_json={k: v for k, v in response.items() if not k.startswith("_")},
        )
        self.db.commit()
        return response

    def list_sync_runs(self, user_context: dict, store_id: UUID) -> list[dict]:
        require_permission(user_context, Permission.SYNC_READ)
        store = self._require_store(user_context, store_id)
        return [self._serialize_sync_run(item) for item in self.sync_repository.list_sync_runs(store.organization_id, store.id)]

    def get_sync_run(self, user_context: dict, store_id: UUID, sync_run_id: UUID) -> dict:
        require_permission(user_context, Permission.SYNC_READ)
        store = self._require_store(user_context, store_id)
        sync_run = self.sync_repository.get_sync_run(store.organization_id, store.id, sync_run_id)
        if sync_run is None:
            raise AppError(code="not_found", message="Sync run not found", status_code=404)
        return self._serialize_sync_run(sync_run)

    def retry_sync_run(self, user_context: dict, store_id: UUID, sync_run_id: UUID, idempotency_key: str | None) -> dict:
        require_permission(user_context, Permission.SYNC_TRIGGER)
        store = self._require_store(user_context, store_id)
        existing_response, _, fingerprint = resolve_idempotent_response(
            self.idempotency_repository,
            organization_id=store.organization_id,
            scope=f"sync:retry:{sync_run_id}",
            idempotency_key=idempotency_key,
            payload={"store_id": str(store.id), "sync_run_id": str(sync_run_id)},
        )
        if existing_response is not None:
            return existing_response
        previous = self.sync_repository.get_sync_run(store.organization_id, store.id, sync_run_id)
        if previous is None:
            raise AppError(code="not_found", message="Sync run not found", status_code=404)
        if previous.status != "failed":
            raise AppError(code="conflict", message="Only failed syncs can be retried", status_code=409)
        integration = self.store_repository.get_integration(store.id)
        sync_run = self.sync_repository.create_sync_run(
            organization_id=store.organization_id,
            store_id=store.id,
            integration_id=integration.id,
            mode="retry_full",
            status="queued",
            triggered_by_user_id=UUID(user_context["user"]["id"]),
            retry_of_sync_run_id=previous.id,
            entity_counts_json={},
            error_details_json={},
        )
        response = self._serialize_sync_run(sync_run)
        response["_enqueue_sync_run"] = True
        self.idempotency_repository.create_record(
            organization_id=store.organization_id,
            scope=f"sync:retry:{sync_run_id}",
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            resource_type="sync_run",
            resource_id=sync_run.id,
            response_json={k: v for k, v in response.items() if not k.startswith("_")},
        )
        self.db.commit()
        return response

    def execute_sync_run(self, sync_run_id: str) -> None:
        workflow_repository = self.workflow_repository
        try:
            sync_run = self.db.get(SyncRun, UUID(sync_run_id))
            if sync_run is None or sync_run.status == "succeeded":
                return
            store = self.store_repository.get_store(sync_run.organization_id, sync_run.store_id)
            integration = self.store_repository.get_integration(sync_run.store_id)
            access_token = self.secret_store.get(integration.secret_reference) if integration and integration.secret_reference else None
            if store is None or integration is None or not access_token:
                raise AppError(code="conflict", message="Store integration is not ready for sync execution", status_code=409)
            workflow = workflow_repository.get_workflow_by_key("store_sync_completed")
            workflow_run = workflow_repository.create_workflow_run(
                organization_id=sync_run.organization_id,
                store_id=sync_run.store_id,
                workflow_id=workflow.id if workflow else None,
                trigger_type="sync_started",
                trigger_entity_type="sync_run",
                trigger_entity_id=sync_run.id,
                status="running",
                input_payload={"sync_run_id": sync_run_id},
                output_payload={},
            )
            sync_run.status = "running"
            sync_run.started_at = datetime.now(timezone.utc)
            self.db.flush()

            products = self.shopify_client.fetch_products(store.domain, access_token)
            customers = {
                item["external_customer_id"]: item
                for item in self.shopify_client.fetch_customers(store.domain, access_token)
            }
            orders = self.shopify_client.fetch_orders(store.domain, access_token)

            imported = {"products": 0, "variants": 0, "customers": 0, "orders": 0}
            for product_payload in products:
                product_payload["last_sync_run_id"] = sync_run.id
                product_payload["last_synced_at"] = datetime.now(timezone.utc)
                product = self.sync_repository.upsert_product(sync_run.organization_id, sync_run.store_id, product_payload)
                imported["products"] += 1
                for variant_payload in product_payload.get("variants", []):
                    variant_payload["last_sync_run_id"] = sync_run.id
                    variant_payload["last_synced_at"] = datetime.now(timezone.utc)
                    self.sync_repository.upsert_variant(sync_run.organization_id, sync_run.store_id, product.id, variant_payload)
                    imported["variants"] += 1

            for customer_payload in customers.values():
                customer_payload["last_sync_run_id"] = sync_run.id
                customer_payload["last_synced_at"] = datetime.now(timezone.utc)
                self.sync_repository.upsert_customer(sync_run.organization_id, sync_run.store_id, customer_payload)
                imported["customers"] += 1

            for order_payload in orders:
                customer_payload = order_payload.get("customer")
                customer_id = None
                if customer_payload:
                    customer_payload["last_sync_run_id"] = sync_run.id
                    customer_payload["last_synced_at"] = datetime.now(timezone.utc)
                    customer = self.sync_repository.upsert_customer(sync_run.organization_id, sync_run.store_id, customer_payload)
                    customer_id = customer.id
                order_payload["customer_id"] = customer_id
                order_payload["last_sync_run_id"] = sync_run.id
                order_payload["last_synced_at"] = datetime.now(timezone.utc)
                order = self.sync_repository.upsert_order(sync_run.organization_id, sync_run.store_id, order_payload)
                self.sync_repository.replace_order_items(sync_run.organization_id, sync_run.store_id, order.id, order_payload.get("items", []))
                imported["orders"] += 1

            self.sync_repository.archive_missing_products(
                sync_run.organization_id,
                sync_run.store_id,
                {str(product["external_product_id"]) for product in products},
                archived_at=datetime.now(timezone.utc),
            )

            sync_run.status = "succeeded"
            sync_run.records_imported = sum(imported.values())
            sync_run.records_failed = 0
            sync_run.entity_counts_json = imported
            sync_run.completed_at = datetime.now(timezone.utc)
            store.last_successful_sync_at = sync_run.completed_at
            integration.last_successful_sync_at = sync_run.completed_at
            workflow_repository.update_workflow_run(
                workflow_run,
                status="succeeded",
                output_payload={"entity_counts": imported},
                completed_at=datetime.now(timezone.utc),
            )
            workflow_repository.create_audit_event(
                organization_id=sync_run.organization_id,
                store_id=sync_run.store_id,
                user_id=sync_run.triggered_by_user_id,
                entity_type="sync_run",
                entity_id=sync_run.id,
                action_type="sync_completed",
                source_type="celery",
                outcome="succeeded",
                metadata_json={"entity_counts": imported},
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            sync_run = self.db.get(SyncRun, UUID(sync_run_id))
            if sync_run is not None:
                message = redact_text(str(exc))
                sync_run.status = "failed"
                sync_run.error_summary = message
                sync_run.completed_at = datetime.now(timezone.utc)
                workflow = workflow_repository.get_workflow_by_key("store_sync_failed")
                workflow_repository.create_workflow_run(
                    organization_id=sync_run.organization_id,
                    store_id=sync_run.store_id,
                    workflow_id=workflow.id if workflow else None,
                    trigger_type="sync_failed",
                    trigger_entity_type="sync_run",
                    trigger_entity_id=sync_run.id,
                    status="failed",
                    input_payload={"sync_run_id": sync_run_id},
                    output_payload={"error": message},
                    error_message=message,
                )
                workflow_repository.create_audit_event(
                    organization_id=sync_run.organization_id,
                    store_id=sync_run.store_id,
                    user_id=sync_run.triggered_by_user_id,
                    entity_type="sync_run",
                    entity_id=sync_run.id,
                    action_type="sync_failed",
                    source_type="celery",
                    outcome="failed",
                    metadata_json={"error": message},
                )
                for user_id in self._sync_failure_recipients(sync_run):
                    workflow_repository.create_notification(
                        organization_id=sync_run.organization_id,
                        store_id=sync_run.store_id,
                        user_id=user_id,
                        type="sync_failed",
                        channel="in_app",
                        title="Store sync failed",
                        body=message,
                        payload_json={"sync_run_id": sync_run_id},
                        status="unread",
                    )
                self.db.commit()
            raise

    def schedule_all_store_syncs(self) -> list[str]:
        queued_sync_run_ids: list[str] = []
        connected_stores = (
            self.db.query(Store)
            .join(Integration, Integration.store_id == Store.id)
            .filter(Store.connection_status == "connected", Integration.status == "connected")
            .all()
        )
        for store in connected_stores:
            if self.sync_repository.get_active_sync_run(store.id):
                continue
            integration = (
                self.db.query(Integration).filter(Integration.store_id == store.id, Integration.provider == "shopify").one_or_none()
            )
            if integration is None:
                continue
            sync_run = self.sync_repository.create_sync_run(
                organization_id=store.organization_id,
                store_id=store.id,
                integration_id=integration.id,
                mode="scheduled_full",
                status="queued",
                triggered_by_user_id=None,
                entity_counts_json={},
                error_details_json={},
            )
            self.db.commit()
            queued_sync_run_ids.append(str(sync_run.id))
        return queued_sync_run_ids

    def _sync_failure_recipients(self, sync_run: SyncRun) -> list[UUID]:
        if sync_run.triggered_by_user_id:
            return [sync_run.triggered_by_user_id]
        users = self.user_repository.list_users_with_any_role(sync_run.organization_id, ["Owner", "Admin"])
        return [user.id for user in users]

    def _require_store(self, user_context: dict, store_id: UUID):
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        store = self.store_repository.get_store(UUID(organization["id"]), store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return store

    @staticmethod
    def _serialize_sync_run(sync_run) -> dict:
        return {
            "id": str(sync_run.id),
            "status": sync_run.status,
            "mode": sync_run.mode,
            "records_imported": sync_run.records_imported,
            "records_failed": sync_run.records_failed,
            "entity_counts_json": sync_run.entity_counts_json,
            "error_summary": sync_run.error_summary,
            "started_at": sync_run.started_at.isoformat() if sync_run.started_at else None,
            "completed_at": sync_run.completed_at.isoformat() if sync_run.completed_at else None,
            "retry_of_sync_run_id": str(sync_run.retry_of_sync_run_id) if sync_run.retry_of_sync_run_id else None,
            "created_at": sync_run.created_at.isoformat(),
        }
