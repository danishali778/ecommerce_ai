from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.core.errors import AppError
from app.core.redaction import redact_text
from app.repositories.models import SyncRun

from .notifications import sync_failure_recipients


def execute_sync_run(module, sync_run_id: str) -> None:
    workflow_repository = module.workflow_repository
    try:
        sync_run = module.db.get(SyncRun, UUID(sync_run_id))
        if sync_run is None or sync_run.status == "succeeded":
            return
        store = module.store_repository.get_store(sync_run.organization_id, sync_run.store_id)
        integration = module.store_repository.get_integration(sync_run.store_id)
        access_token = module.secret_store.get(integration.secret_reference) if integration and integration.secret_reference else None
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
        module.db.flush()

        products = module.shopify_client.fetch_products(store.domain, access_token)
        customers = {
            item["external_customer_id"]: item
            for item in module.shopify_client.fetch_customers(store.domain, access_token)
        }
        orders = module.shopify_client.fetch_orders(store.domain, access_token)

        imported = {"products": 0, "variants": 0, "customers": 0, "orders": 0}
        for product_payload in products:
            product_payload["last_sync_run_id"] = sync_run.id
            product_payload["last_synced_at"] = datetime.now(timezone.utc)
            product = module.sync_repository.upsert_product(sync_run.organization_id, sync_run.store_id, product_payload)
            imported["products"] += 1
            for variant_payload in product_payload.get("variants", []):
                variant_payload["last_sync_run_id"] = sync_run.id
                variant_payload["last_synced_at"] = datetime.now(timezone.utc)
                module.sync_repository.upsert_variant(sync_run.organization_id, sync_run.store_id, product.id, variant_payload)
                imported["variants"] += 1

        for customer_payload in customers.values():
            customer_payload["last_sync_run_id"] = sync_run.id
            customer_payload["last_synced_at"] = datetime.now(timezone.utc)
            module.sync_repository.upsert_customer(sync_run.organization_id, sync_run.store_id, customer_payload)
            imported["customers"] += 1

        for order_payload in orders:
            customer_payload = order_payload.get("customer")
            customer_id = None
            if customer_payload:
                customer_payload["last_sync_run_id"] = sync_run.id
                customer_payload["last_synced_at"] = datetime.now(timezone.utc)
                customer = module.sync_repository.upsert_customer(sync_run.organization_id, sync_run.store_id, customer_payload)
                customer_id = customer.id
            order_payload["customer_id"] = customer_id
            order_payload["last_sync_run_id"] = sync_run.id
            order_payload["last_synced_at"] = datetime.now(timezone.utc)
            order = module.sync_repository.upsert_order(sync_run.organization_id, sync_run.store_id, order_payload)
            module.sync_repository.replace_order_items(sync_run.organization_id, sync_run.store_id, order.id, order_payload.get("items", []))
            imported["orders"] += 1

        module.sync_repository.archive_missing_products(
            sync_run.organization_id,
            sync_run.store_id,
            {str(product["external_product_id"]) for product in products},
            archived_at=datetime.now(timezone.utc),
        )

        post_processing: dict[str, dict] = {}
        for key, handler in {
            "fraud": module.fraud_module.process_sync_run,
            "inventory": module.inventory_module.process_sync_run,
        }.items():
            try:
                post_processing[key] = handler(sync_run)
            except Exception as post_processing_exc:  # noqa: BLE001
                redacted_message = redact_text(str(post_processing_exc))
                post_processing[key] = {"error": redacted_message}
                workflow_repository.create_audit_event(
                    organization_id=sync_run.organization_id,
                    store_id=sync_run.store_id,
                    user_id=sync_run.triggered_by_user_id,
                    entity_type="sync_run",
                    entity_id=sync_run.id,
                    action_type=f"{key}_post_processing_failed",
                    source_type="celery",
                    outcome="failed",
                    metadata_json={"error": redacted_message},
                )

        sync_run.status = "succeeded"
        sync_run.records_imported = sum(imported.values())
        sync_run.records_failed = 0
        sync_run.entity_counts_json = imported | post_processing
        sync_run.completed_at = datetime.now(timezone.utc)
        store.last_successful_sync_at = sync_run.completed_at
        integration.last_successful_sync_at = sync_run.completed_at
        workflow_repository.update_workflow_run(
            workflow_run,
            status="succeeded",
            output_payload={"entity_counts": imported, "post_processing": post_processing},
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
            metadata_json={"entity_counts": imported, "post_processing": post_processing},
        )
        module.db.commit()
    except Exception as exc:  # noqa: BLE001
        module.db.rollback()
        sync_run = module.db.get(SyncRun, UUID(sync_run_id))
        if sync_run is not None:
            message = redact_text(str(exc))
            sync_run.status = "failed"
            sync_run.error_summary = message
            sync_run.error_details_json = exc.details if isinstance(exc, AppError) else {
                "exception_type": exc.__class__.__name__,
            }
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
            for user_id in sync_failure_recipients(module, sync_run):
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
            module.db.commit()
        raise

