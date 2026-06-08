from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.core.authz import require_any_permission, require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.modules.notifications.delivery import queue_external_deliveries
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.models import Workflow, WorkflowRun
from app.repositories.notification_repository import NotificationRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workflow_repository import WorkflowRepository


ALLOWED_TRIGGERS = {
    "sync.completed": {"sync.records_imported", "sync.records_failed"},
    "order.imported": {"order.total", "order.risk_score", "order.payment_status"},
    "inventory.below_threshold": {"inventory.current_quantity", "inventory.threshold_value"},
    "pricing.recommendation.created": {"pricing.recommended_price", "pricing.validation_status", "pricing.requires_approval"},
    "approval.pending": {"approval.action_type", "approval.entity_type"},
    "workflow.failed": {"workflow.error_count", "workflow.trigger_type"},
}

ALLOWED_ACTIONS = {
    "create_alert",
    "create_approval",
    "enqueue_agent",
    "send_external_notification",
    "create_inventory_alert",
    "create_pricing_recommendation",
    "log_audit_event",
}


def serialize_workflow(workflow) -> dict:
    return {
        "id": str(workflow.id),
        "store_id": str(workflow.store_id) if workflow.store_id else None,
        "name": workflow.name,
        "key": workflow.key,
        "description": workflow.description,
        "phase_scope": workflow.phase_scope,
        "trigger": workflow.trigger_type,
        "condition_groups": workflow.condition_groups_json or [],
        "actions": workflow.actions_json or [],
        "approval_required": workflow.approval_required,
        "enabled": workflow.is_active,
        "is_system_defined": workflow.is_system_defined,
        "version_number": workflow.version_number,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
    }


class WorkflowModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.notification_repository = NotificationRepository(db)
        self.approval_repository = ApprovalRepository(db)
        self.inventory_repository = InventoryRepository(db)
        self.user_repository = UserRepository(db)

    def list_workflows(self, user_context: dict, store_id: UUID) -> list[dict]:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.WORKFLOWS_READ, Permission.WORKFLOWS_MANAGE])
        workflows = self.workflow_repository.list_workflows(organization_id, store_id)
        return [serialize_workflow(workflow) for workflow in workflows]

    def create_workflow(self, user_context: dict, store_id: UUID, payload) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.WORKFLOWS_MANAGE)
        self._validate_definition(payload.trigger, payload.condition_groups, payload.actions)
        key = f"wf_{store_id.hex[:8]}_{uuid4().hex[:10]}"
        workflow = self.workflow_repository.create_workflow(
            organization_id=organization_id,
            store_id=store_id,
            name=payload.name,
            key=key,
            description=payload.description,
            phase_scope=payload.phase_scope,
            trigger_type=payload.trigger,
            condition_json={"groups_count": len(payload.condition_groups)},
            action_type=payload.actions[0].type if payload.actions else "log_audit_event",
            condition_groups_json=[group.model_dump(mode="json") for group in payload.condition_groups],
            actions_json=[action.model_dump(mode="json") for action in payload.actions],
            approval_required=payload.approval_required,
            is_system_defined=False,
            is_active=payload.enabled,
            version_number=1,
            created_by_user_id=UUID(user_context["user"]["id"]),
            updated_by_user_id=UUID(user_context["user"]["id"]),
        )
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="workflow_definition",
            entity_id=workflow.id,
            action_type="created",
            source_type="api",
            outcome="succeeded",
            metadata_json={"trigger_type": workflow.trigger_type},
        )
        self.db.commit()
        return serialize_workflow(workflow)

    def get_workflow(self, user_context: dict, store_id: UUID, workflow_id: UUID) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.WORKFLOWS_READ, Permission.WORKFLOWS_MANAGE])
        workflow = self.workflow_repository.get_workflow(organization_id, store_id, workflow_id)
        if workflow is None:
            raise AppError(code="not_found", message="Workflow not found", status_code=404)
        return serialize_workflow(workflow)

    def update_workflow(self, user_context: dict, store_id: UUID, workflow_id: UUID, payload) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.WORKFLOWS_MANAGE)
        workflow = self.workflow_repository.get_workflow(organization_id, store_id, workflow_id)
        if workflow is None:
            raise AppError(code="not_found", message="Workflow not found", status_code=404)
        if workflow.is_system_defined:
            raise AppError(code="forbidden", message="System workflows cannot be edited", status_code=403)
        trigger = payload.trigger or workflow.trigger_type
        condition_groups = payload.condition_groups or workflow.condition_groups_json or []
        actions = payload.actions or workflow.actions_json or []
        self._validate_definition(trigger, condition_groups, actions)
        updates = {
            "updated_by_user_id": UUID(user_context["user"]["id"]),
            "version_number": workflow.version_number + 1,
        }
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.description is not None:
            updates["description"] = payload.description
        if payload.enabled is not None:
            updates["is_active"] = payload.enabled
        if payload.trigger is not None:
            updates["trigger_type"] = payload.trigger
        if payload.condition_groups is not None:
            updates["condition_groups_json"] = [group.model_dump(mode="json") for group in payload.condition_groups]
            updates["condition_json"] = {"groups_count": len(payload.condition_groups)}
        if payload.actions is not None:
            updates["actions_json"] = [action.model_dump(mode="json") for action in payload.actions]
            updates["action_type"] = payload.actions[0].type if payload.actions else workflow.action_type
        if payload.approval_required is not None:
            updates["approval_required"] = payload.approval_required
        workflow = self.workflow_repository.update_workflow(workflow, **updates)
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="workflow_definition",
            entity_id=workflow.id,
            action_type="updated",
            source_type="api",
            outcome="succeeded",
            metadata_json={"version_number": workflow.version_number},
        )
        self.db.commit()
        return serialize_workflow(workflow)

    def delete_workflow(self, user_context: dict, store_id: UUID, workflow_id: UUID) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.WORKFLOWS_MANAGE)
        workflow = self.workflow_repository.get_workflow(organization_id, store_id, workflow_id)
        if workflow is None:
            raise AppError(code="not_found", message="Workflow not found", status_code=404)
        if workflow.is_system_defined:
            raise AppError(code="forbidden", message="System workflows cannot be deleted", status_code=403)
        self.workflow_repository.delete_workflow(workflow)
        self.db.commit()
        return {"deleted": True, "workflow_id": str(workflow.id)}

    def enable_workflow(self, user_context: dict, store_id: UUID, workflow_id: UUID) -> dict:
        return self._set_enabled(user_context, store_id, workflow_id, True)

    def disable_workflow(self, user_context: dict, store_id: UUID, workflow_id: UUID) -> dict:
        return self._set_enabled(user_context, store_id, workflow_id, False)

    def test_workflow(self, user_context: dict, store_id: UUID, workflow_id: UUID, payload) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.WORKFLOWS_MANAGE)
        workflow = self.workflow_repository.get_workflow(organization_id, store_id, workflow_id)
        if workflow is None:
            raise AppError(code="not_found", message="Workflow not found", status_code=404)
        matched = self._evaluate_condition_groups(workflow.condition_groups_json or [], payload.event_payload)
        workflow_run = self.workflow_repository.create_workflow_run(
            organization_id=organization_id,
            store_id=store_id,
            workflow_id=workflow.id,
            trigger_type=workflow.trigger_type,
            trigger_entity_type=payload.event_entity_type,
            trigger_entity_id=payload.event_entity_id,
            status="succeeded",
            input_payload=payload.event_payload,
            output_payload={"matched": matched, "dry_run": True},
            error_message=None,
            retry_count=0,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        self.db.commit()
        return {
            "status": "succeeded",
            "matched": matched,
            "workflow_run_id": str(workflow_run.id),
            "results": {"dry_run": True, "actions": workflow.actions_json or []},
        }

    def execute_workflow_run(self, workflow_run_id: str, trace_id: str | None = None) -> dict:
        workflow_run = self.db.get(WorkflowRun, UUID(workflow_run_id))
        if workflow_run is None:
            raise AppError(code="not_found", message="Workflow run not found", status_code=404)
        workflow = self.db.get(Workflow, workflow_run.workflow_id) if workflow_run.workflow_id else None
        if workflow is None:
            raise AppError(code="not_found", message="Workflow definition not found", status_code=404)
        self.workflow_repository.update_workflow_run(
            workflow_run,
            status="running",
            trace_id=trace_id or workflow_run.trace_id,
            started_at=workflow_run.started_at or datetime.now(timezone.utc),
            completed_at=None,
        )
        self.db.flush()
        deferred_jobs: list[dict] = []
        try:
            result = self._execute_workflow(
                organization_id=workflow_run.organization_id,
                store_id=workflow_run.store_id,
                workflow=workflow,
                workflow_run=workflow_run,
                entity_type=workflow_run.trigger_entity_type,
                entity_id=workflow_run.trigger_entity_id,
                payload=workflow_run.input_payload or {},
                trace_id=trace_id or workflow_run.trace_id,
                deferred_jobs=deferred_jobs,
            )
            self.db.commit()
            self._dispatch_deferred_jobs(deferred_jobs)
            return result
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            workflow_run = self.db.get(WorkflowRun, UUID(workflow_run_id))
            workflow = self.db.get(Workflow, workflow_run.workflow_id) if workflow_run and workflow_run.workflow_id else workflow
            if workflow_run is None or workflow is None:
                raise
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="failed",
                trace_id=trace_id or workflow_run.trace_id,
                output_payload={"matched": True},
                completed_at=datetime.now(timezone.utc),
                error_message=str(exc),
            )
            self.workflow_repository.create_audit_event(
                organization_id=workflow_run.organization_id,
                store_id=workflow_run.store_id,
                user_id=None,
                entity_type="workflow_definition",
                entity_id=workflow.id,
                action_type="execution_failed",
                source_type="workflow_engine",
                outcome="failed",
                metadata_json={"error": str(exc), "trigger_type": workflow.trigger_type},
            )
            raise

    def evaluate_event(
        self,
        *,
        organization_id: UUID,
        store_id: UUID,
        trigger_type: str,
        entity_type: str,
        entity_id: UUID | None,
        payload: dict,
        trace_id: str | None = None,
    ) -> dict:
        workflows = self.workflow_repository.list_enabled_workflows_for_trigger(organization_id, store_id, trigger_type)
        processed = 0
        failed = 0
        deferred_jobs: list[dict] = []
        for workflow in workflows:
            processed += 1
            workflow_run = self.workflow_repository.create_workflow_run(
                organization_id=organization_id,
                store_id=store_id,
                workflow_id=workflow.id,
                trigger_type=trigger_type,
                trigger_entity_type=entity_type,
                trigger_entity_id=entity_id,
                status="running",
                trace_id=trace_id,
                input_payload=payload,
                output_payload={},
                error_message=None,
                retry_count=0,
                started_at=datetime.now(timezone.utc),
                completed_at=None,
            )
            try:
                self._execute_workflow(
                    organization_id=organization_id,
                    store_id=store_id,
                    workflow=workflow,
                    workflow_run=workflow_run,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    payload=payload,
                    trace_id=trace_id,
                    deferred_jobs=deferred_jobs,
                )
            except Exception as exc:  # noqa: BLE001
                failed += 1
                self.workflow_repository.update_workflow_run(
                    workflow_run,
                    status="failed",
                    trace_id=trace_id or workflow_run.trace_id,
                    output_payload={"matched": True},
                    completed_at=datetime.now(timezone.utc),
                    error_message=str(exc),
                )
                self.workflow_repository.create_audit_event(
                    organization_id=organization_id,
                    store_id=store_id,
                    user_id=None,
                    entity_type="workflow_definition",
                    entity_id=workflow.id,
                    action_type="execution_failed",
                    source_type="workflow_engine",
                    outcome="failed",
                    metadata_json={"error": str(exc), "trigger_type": trigger_type},
                )
                if trigger_type != "workflow.failed":
                    from .events import emit_workflow_event

                    emit_workflow_event(
                        organization_id=organization_id,
                        store_id=store_id,
                        trigger_type="workflow.failed",
                        entity_type="workflow_run",
                        entity_id=workflow_run.id,
                        trace_id=trace_id or workflow_run.trace_id,
                        payload={"workflow_run_id": str(workflow_run.id), "error_count": 1, "workflow.trigger_type": trigger_type},
                    )
        self.db.commit()
        self._dispatch_deferred_jobs(deferred_jobs)
        return {"processed": processed, "failed": failed}

    def _execute_workflow(
        self,
        *,
        organization_id: UUID,
        store_id: UUID,
        workflow,
        workflow_run,
        entity_type: str,
        entity_id: UUID | None,
        payload: dict,
        trace_id: str | None = None,
        deferred_jobs: list[dict] | None = None,
    ) -> dict:
        matched = self._evaluate_condition_groups(workflow.condition_groups_json or [], payload)
        results = []
        if matched:
            for action in workflow.actions_json or []:
                results.append(
                    self._execute_action(
                        organization_id=organization_id,
                        store_id=store_id,
                        workflow=workflow,
                        action=action,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        payload=payload,
                        deferred_jobs=deferred_jobs or [],
                    )
                )
        self.workflow_repository.update_workflow_run(
            workflow_run,
            status="succeeded",
            trace_id=trace_id or workflow_run.trace_id,
            output_payload={"matched": matched, "results": results},
            completed_at=datetime.now(timezone.utc),
            error_message=None,
        )
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=None,
            entity_type="workflow_definition",
            entity_id=workflow.id,
            action_type="executed",
            source_type="workflow_engine",
            outcome="succeeded",
            metadata_json={"trigger_type": workflow.trigger_type, "matched": matched},
        )
        return {"matched": matched, "results": results}

    def _set_enabled(self, user_context: dict, store_id: UUID, workflow_id: UUID, enabled: bool) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.WORKFLOWS_MANAGE)
        workflow = self.workflow_repository.get_workflow(organization_id, store_id, workflow_id)
        if workflow is None:
            raise AppError(code="not_found", message="Workflow not found", status_code=404)
        if workflow.is_system_defined:
            raise AppError(code="forbidden", message="System workflows cannot be toggled here", status_code=403)
        workflow = self.workflow_repository.update_workflow(
            workflow,
            is_active=enabled,
            updated_by_user_id=UUID(user_context["user"]["id"]),
            version_number=workflow.version_number + 1,
        )
        self.db.commit()
        return serialize_workflow(workflow)

    def _execute_action(
        self,
        *,
        organization_id: UUID,
        store_id: UUID,
        workflow,
        action: dict,
        entity_type: str,
        entity_id: UUID | None,
        payload: dict,
        deferred_jobs: list[dict],
    ) -> dict:
        action_type = action["type"]
        params = action.get("params", {})
        if action_type == "create_alert":
            notification = self.notification_repository.create_notification(
                organization_id=organization_id,
                store_id=store_id,
                user_id=self._pick_recipient_user_id(organization_id),
                type="workflow_alert",
                channel="in_app",
                title=params.get("title", f"Workflow alert: {workflow.name}"),
                body=params.get("body", "A workflow condition matched and created an alert."),
                payload_json={"workflow_id": str(workflow.id), "entity_type": entity_type, "entity_id": str(entity_id) if entity_id else None},
                status="unread",
            )
            queue_external_deliveries(self.db, notification, params.get("event_type", "workflow_alert"))
            return {"type": action_type, "notification_id": str(notification.id)}
        if action_type == "create_approval":
            approval = self.approval_repository.create_approval(
                organization_id=organization_id,
                store_id=store_id,
                action_type=params.get("approval_action_type", "workflow_manual_review"),
                entity_type=params.get("entity_type", entity_type),
                entity_id=UUID(str(entity_id or params.get("entity_id"))),
                workflow_run_id=None,
                agent_run_id=None,
                proposed_action_json={"params": params, "payload": payload},
                source_snapshot_hash=str(uuid4()),
                source_snapshot_created_at=datetime.now(timezone.utc),
                reasoning=params.get("reasoning", f"Workflow {workflow.name} requested manual approval."),
                status="pending",
                review_notes=None,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                execution_status=None,
                execution_error=None,
                idempotency_key=f"workflow-approval:{workflow.id}:{uuid4().hex}",
                requested_by_user_id=None,
                reviewed_by_user_id=None,
                reviewed_at=None,
                last_execution_attempt_at=None,
                retry_count=0,
            )
            return {"type": action_type, "approval_id": str(approval.id)}
        if action_type == "send_external_notification":
            notification = self.notification_repository.create_notification(
                organization_id=organization_id,
                store_id=store_id,
                user_id=self._pick_recipient_user_id(organization_id),
                type="workflow_external_notification",
                channel="in_app",
                title=params.get("title", f"Workflow notification: {workflow.name}"),
                body=params.get("body", "A workflow emitted an external notification."),
                payload_json={"workflow_id": str(workflow.id), "payload": payload},
                status="unread",
            )
            deliveries = queue_external_deliveries(self.db, notification, params.get("event_type", "workflow_alert"))
            return {"type": action_type, "delivery_count": len(deliveries)}
        if action_type == "create_inventory_alert":
            variant_id = UUID(str(payload.get("variant_id") or params.get("variant_id")))
            existing = self.inventory_repository.get_open_alert_for_variant(organization_id, store_id, variant_id)
            if existing is None:
                alert = self.inventory_repository.create_alert(
                    organization_id=organization_id,
                    store_id=store_id,
                    product_id=UUID(str(payload.get("product_id") or params.get("product_id"))),
                    variant_id=variant_id,
                    threshold_value=int(payload.get("threshold_value") or params.get("threshold_value") or 0),
                    current_quantity=int(payload.get("current_quantity") or params.get("current_quantity") or 0),
                    status="open",
                    resolved_at=None,
                )
            else:
                alert = self.inventory_repository.update_alert(
                    existing,
                    current_quantity=int(payload.get("current_quantity") or params.get("current_quantity") or existing.current_quantity),
                )
            return {"type": action_type, "alert_id": str(alert.id)}
        if action_type == "create_pricing_recommendation":
            from app.modules.pricing import PricingModule

            pricing_module = PricingModule(self.db)
            reference_input = pricing_module.pricing_repository.create_reference_input(
                organization_id=organization_id,
                store_id=store_id,
                pricing_rule_id=UUID(params["pricing_rule_id"]) if params.get("pricing_rule_id") else None,
                product_id=UUID(str(payload.get("product_id") or params.get("product_id"))) if payload.get("product_id") or params.get("product_id") else None,
                variant_id=UUID(str(payload.get("variant_id") or params.get("variant_id"))) if payload.get("variant_id") or params.get("variant_id") else None,
                source_type="workflow",
                reference_label=params.get("reference_label"),
                import_batch_id=None,
                reference_price=None,
                cost_override=None,
                margin_floor_override=None,
                price_ceiling_override=None,
                payload_json=payload,
                created_by_user_id=None,
            )
            run_state = pricing_module.agent_runner.start_generation(
                organization_id=organization_id,
                store_id=store_id,
                reference_input=reference_input,
                triggered_by_user_id=None,
            )
            deferred_jobs.append({"type": "pricing_recommendation", "agent_run_id": run_state["agent_run_id"]})
            return {
                "type": action_type,
                "reference_input_id": str(reference_input.id),
                "agent_run_id": run_state["agent_run_id"],
                "workflow_run_id": run_state["workflow_run_id"],
                "status": "queued",
            }
        if action_type == "enqueue_agent":
            return {"type": action_type, "status": "queued", "agent_type": params.get("agent_type")}
        if action_type == "log_audit_event":
            self.workflow_repository.create_audit_event(
                organization_id=organization_id,
                store_id=store_id,
                user_id=None,
                entity_type=params.get("entity_type", entity_type),
                entity_id=UUID(str(entity_id)) if entity_id else None,
                action_type=params.get("action_type", "workflow_logged_event"),
                source_type="workflow_engine",
                outcome="succeeded",
                metadata_json={"workflow_id": str(workflow.id), "payload": payload},
            )
            return {"type": action_type, "status": "logged"}
        raise AppError(code="invalid_workflow_action", message=f"Unsupported workflow action: {action_type}", status_code=422)

    @staticmethod
    def _dispatch_deferred_jobs(deferred_jobs: list[dict]) -> None:
        if not deferred_jobs:
            return
        from app.tasks.pricing import generate_pricing_recommendation

        for job in deferred_jobs:
            if job["type"] == "pricing_recommendation":
                generate_pricing_recommendation.delay(job["agent_run_id"], None)

    def _validate_definition(self, trigger_type: str, condition_groups, actions) -> None:
        if trigger_type not in ALLOWED_TRIGGERS:
            raise AppError(code="invalid_workflow_trigger", message="Unsupported workflow trigger", status_code=422)
        if not actions:
            raise AppError(code="invalid_workflow_actions", message="At least one workflow action is required", status_code=422)
        for group in condition_groups:
            conditions = group.conditions if hasattr(group, "conditions") else group.get("conditions", [])
            for condition in conditions:
                field_name = condition.field if hasattr(condition, "field") else condition["field"]
                if field_name not in ALLOWED_TRIGGERS[trigger_type]:
                    raise AppError(code="invalid_workflow_condition", message=f"Unsupported field for trigger: {field_name}", status_code=422)
        for action in actions:
            action_type = action.type if hasattr(action, "type") else action["type"]
            if action_type not in ALLOWED_ACTIONS:
                raise AppError(code="invalid_workflow_action", message=f"Unsupported workflow action: {action_type}", status_code=422)

    @staticmethod
    def _evaluate_condition_groups(condition_groups: list[dict], payload: dict) -> bool:
        if not condition_groups:
            return True
        group_results: list[bool] = []
        for group in condition_groups:
            match = group.get("match", "all")
            condition_results = []
            for condition in group.get("conditions", []):
                actual = payload.get(condition["field"])
                operator = condition["operator"]
                expected = condition["value"]
                if operator == "gt":
                    condition_results.append(actual is not None and actual > expected)
                elif operator == "gte":
                    condition_results.append(actual is not None and actual >= expected)
                elif operator == "lt":
                    condition_results.append(actual is not None and actual < expected)
                elif operator == "lte":
                    condition_results.append(actual is not None and actual <= expected)
                elif operator == "eq":
                    condition_results.append(actual == expected)
                elif operator == "neq":
                    condition_results.append(actual != expected)
                elif operator == "in":
                    condition_results.append(actual in expected)
                elif operator == "bool_is":
                    condition_results.append(bool(actual) is bool(expected))
                else:
                    condition_results.append(False)
            group_results.append(all(condition_results) if match == "all" else any(condition_results))
        return all(group_results)

    def _pick_recipient_user_id(self, organization_id: UUID) -> UUID:
        users = self.user_repository.list_users_with_any_role(organization_id, ["Owner", "Admin", "Manager"])
        if not users:
            raise AppError(code="workflow_notification_target_missing", message="No operator user available for workflow notification", status_code=409)
        return users[0].id

    def require_store_access(self, user_context: dict, store_id: UUID) -> UUID:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        organization_id = UUID(organization["id"])
        store = self.store_repository.get_store(organization_id, store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return organization_id
