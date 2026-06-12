from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import json
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from app.agents.inventory.prompts import build_inventory_reorder_prompt
from app.agents.inventory.schemas import InventoryAgentOutput
from app.core.errors import AppError
from app.core.redaction import redact_text
from app.llm.provider import LLMProvider
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.models import AgentRun, InventoryAlert, Product, ProductVariant, SupplierReorderDraft, WorkflowRun
from app.repositories.sync_repository import SyncRepository
from app.repositories.workflow_repository import WorkflowRepository


class InventoryAgentRunner:
    def __init__(self, db) -> None:
        self.db = db
        self.inventory_repository = InventoryRepository(db)
        self.sync_repository = SyncRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.llm_provider = LLMProvider()

    def start_generation(
        self,
        *,
        organization_id: UUID,
        store_id: UUID,
        alert: InventoryAlert,
        triggered_by_user_id: UUID | None,
        trace_id: str | None = None,
    ) -> dict:
        workflow = self.workflow_repository.ensure_system_workflow(
            key="inventory_reorder_generated",
            name="Inventory Reorder Suggestion Generated",
            phase_scope="p1",
            trigger_type="inventory.below_threshold",
            action_type="inventory_reorder_saved",
        )
        workflow_run = self.workflow_repository.create_workflow_run(
            organization_id=organization_id,
            store_id=store_id,
            workflow_id=workflow.id,
            trigger_type="inventory.below_threshold",
            trigger_entity_type="inventory_alert",
            trigger_entity_id=alert.id,
            status="queued",
            trace_id=trace_id,
            input_payload={"inventory_alert_id": str(alert.id)},
            output_payload={},
        )
        agent_run = self.workflow_repository.create_agent_run(
            organization_id=organization_id,
            store_id=store_id,
            agent_type="inventory_reorder",
            user_id=triggered_by_user_id,
            workflow_run_id=workflow_run.id,
            input_summary=f"Generate reorder suggestion for inventory alert {alert.id}",
            retrieved_context_summary=None,
            output_summary=None,
            tool_calls_json=[],
            model_name=self.llm_provider.model,
            status="queued",
            trace_id=trace_id,
        )
        return {
            "workflow_run_id": str(workflow_run.id),
            "agent_run_id": str(agent_run.id),
            "status": workflow_run.status,
        }

    def execute_generation(self, agent_run_id: str, trace_id: str | None = None) -> dict | None:
        agent_run = self.db.get(AgentRun, UUID(agent_run_id))
        if agent_run is None:
            return None
        workflow_run = self.db.get(WorkflowRun, agent_run.workflow_run_id) if agent_run.workflow_run_id else None
        alert_id = (workflow_run.input_payload or {}).get("inventory_alert_id") if workflow_run else None
        alert = self.db.get(InventoryAlert, UUID(alert_id)) if alert_id else None
        if workflow_run is None or alert is None:
            self._mark_failed(agent_run, workflow_run, "Inventory agent context is incomplete")
            self.db.commit()
            return None

        variant = self.sync_repository.get_variant(alert.organization_id, alert.store_id, alert.variant_id)
        product = self.sync_repository.get_product(alert.organization_id, alert.store_id, alert.product_id)
        if variant is None or product is None:
            self._mark_failed(agent_run, workflow_run, "Inventory agent missing product or variant context")
            self.db.commit()
            return None

        try:
            now = datetime.now(timezone.utc)
            self.workflow_repository.update_agent_run(agent_run, status="running", trace_id=trace_id or agent_run.trace_id)
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="running",
                trace_id=trace_id or workflow_run.trace_id,
                started_at=workflow_run.started_at or now,
            )
            existing_suggestion = self.inventory_repository.get_active_suggestion_for_alert(alert.id)
            existing_draft = self.inventory_repository.get_draft_for_suggestion(existing_suggestion.id) if existing_suggestion else None
            output = self._generate_output(
                product=product,
                variant=variant,
                alert=alert,
                existing_suggestion=existing_suggestion,
                existing_draft=existing_draft,
            )
            review_reason_code = output.review_reason_code
            if output.confidence_score < 0.65 and not review_reason_code:
                review_reason_code = "low_confidence"
            if output.needs_human_review and not review_reason_code:
                review_reason_code = "inventory_review_required"
            suggested_quantity = self._validated_quantity(output.recommended_quantity)
            suggestion = existing_suggestion
            suggestion_status = "drafted" if output.supplier_draft and output.supplier_draft.body else "open"
            payload = {
                "agent_run_id": agent_run.id,
                "recommended_quantity": suggested_quantity,
                "current_quantity": alert.current_quantity,
                "threshold_value": alert.threshold_value,
                "rationale_json": output.rationale_json,
                "rationale_summary": output.rationale_summary,
                "urgency": output.urgency,
                "confidence_score": Decimal(str(output.confidence_score)),
                "needs_human_review": output.needs_human_review,
                "review_reason_code": review_reason_code,
                "status": suggestion_status,
            }
            if suggestion is None:
                suggestion = self.inventory_repository.create_suggestion(
                    organization_id=alert.organization_id,
                    store_id=alert.store_id,
                    inventory_alert_id=alert.id,
                    product_id=alert.product_id,
                    variant_id=alert.variant_id,
                    **payload,
                )
            else:
                self.inventory_repository.update_suggestion(suggestion, **payload)

            draft = existing_draft
            if output.supplier_draft and any(
                [output.supplier_draft.vendor_name, output.supplier_draft.recipient_email, output.supplier_draft.subject, output.supplier_draft.body]
            ):
                vendor_name = output.supplier_draft.vendor_name or (draft.vendor_name if draft else "Supplier")
                subject = output.supplier_draft.subject or (draft.subject if draft else f"Reorder request for variant {alert.variant_id}")
                body = output.supplier_draft.body or (draft.body if draft else "")
                recipient_email = output.supplier_draft.recipient_email if output.supplier_draft.recipient_email is not None else (draft.recipient_email if draft else None)
                if draft is None:
                    draft = self.inventory_repository.create_draft(
                        organization_id=alert.organization_id,
                        store_id=alert.store_id,
                        reorder_suggestion_id=suggestion.id,
                        vendor_name=vendor_name,
                        recipient_email=recipient_email,
                        subject=subject,
                        body=body,
                        status="draft",
                        created_by_user_id=agent_run.user_id,
                    )
                else:
                    self.inventory_repository.update_draft(
                        draft,
                        vendor_name=vendor_name,
                        recipient_email=recipient_email,
                        subject=subject,
                        body=body,
                        status="draft",
                    )

            self.workflow_repository.create_audit_event(
                organization_id=alert.organization_id,
                store_id=alert.store_id,
                user_id=agent_run.user_id,
                entity_type="reorder_suggestion",
                entity_id=suggestion.id,
                action_type="agent_generated",
                source_type="agent",
                outcome="review_required" if output.needs_human_review else "succeeded",
                metadata_json={
                    "agent_type": agent_run.agent_type,
                    "urgency": output.urgency,
                    "confidence_score": output.confidence_score,
                },
            )
            self.workflow_repository.update_agent_run(
                agent_run,
                status="succeeded",
                trace_id=trace_id or agent_run.trace_id,
                retrieved_context_summary=f"Variant {variant.id} current_quantity={alert.current_quantity} threshold={alert.threshold_value}",
                output_summary=redact_text(output.rationale_summary),
            )
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="succeeded",
                trace_id=trace_id or workflow_run.trace_id,
                output_payload={
                    "reorder_suggestion_id": str(suggestion.id),
                    "supplier_draft_id": str(draft.id) if draft else None,
                    "agent_run_id": str(agent_run.id),
                },
                completed_at=datetime.now(timezone.utc),
            )
            self.db.commit()
            return {
                "reorder_suggestion_id": str(suggestion.id),
                "supplier_draft_id": str(draft.id) if draft else None,
                "workflow_run_id": str(workflow_run.id),
                "agent_run_id": str(agent_run.id),
                "status": suggestion.status,
            }
        except Exception as exc:  # noqa: BLE001
            self._mark_failed(agent_run, workflow_run, str(exc))
            self.db.commit()
            raise

    def _generate_output(
        self,
        *,
        product: Product,
        variant: ProductVariant,
        alert: InventoryAlert,
        existing_suggestion,
        existing_draft: SupplierReorderDraft | None,
    ) -> InventoryAgentOutput:
        def generate_node(state: dict) -> dict:
            prompt = build_inventory_reorder_prompt(
                product_context=state["product_context"],
                variant_context=state["variant_context"],
                inventory_context=state["inventory_context"],
                existing_suggestion=state["existing_suggestion"],
                existing_supplier_draft=state["existing_supplier_draft"],
            )
            raw = self.llm_provider.generate_structured_json(prompt)
            output = InventoryAgentOutput.model_validate(self._normalize_output(raw))
            return {"result": output}

        graph = StateGraph(dict)
        graph.add_node("generate", generate_node)
        graph.add_edge(START, "generate")
        graph.add_edge("generate", END)
        result = graph.compile().invoke(
            {
                "product_context": {
                    "id": str(product.id),
                    "title": product.title,
                    "vendor": product.vendor,
                    "category": product.category,
                },
                "variant_context": {
                    "id": str(variant.id),
                    "sku": variant.sku,
                    "title": variant.title,
                    "price": str(variant.price),
                    "cost": str(variant.cost) if variant.cost is not None else None,
                },
                "inventory_context": {
                    "current_quantity": alert.current_quantity,
                    "threshold_value": alert.threshold_value,
                    "existing_status": alert.status,
                },
                "existing_suggestion": {
                    "id": str(existing_suggestion.id),
                    "recommended_quantity": existing_suggestion.recommended_quantity,
                    "status": existing_suggestion.status,
                }
                if existing_suggestion
                else None,
                "existing_supplier_draft": {
                    "vendor_name": existing_draft.vendor_name,
                    "recipient_email": existing_draft.recipient_email,
                    "subject": existing_draft.subject,
                    "body": existing_draft.body,
                }
                if existing_draft
                else None,
            }
        )
        return result["result"]

    @staticmethod
    def _normalize_output(raw: dict | None) -> dict:
        normalized = dict(raw or {})

        for field in ("rationale_summary", "review_reason_code"):
            value = normalized.get(field)
            if value is None:
                continue
            if isinstance(value, (dict, list)):
                normalized[field] = json.dumps(value, ensure_ascii=True)
            else:
                normalized[field] = str(value)

        supplier_draft = normalized.get("supplier_draft")
        if supplier_draft is None:
            return normalized

        if not isinstance(supplier_draft, dict):
            supplier_draft = {"body": supplier_draft}
        else:
            supplier_draft = dict(supplier_draft)

        for field in ("vendor_name", "recipient_email", "subject", "body"):
            value = supplier_draft.get(field)
            if value is None:
                continue
            if isinstance(value, (dict, list)):
                supplier_draft[field] = json.dumps(value, ensure_ascii=True)
            else:
                supplier_draft[field] = str(value)

        normalized["supplier_draft"] = supplier_draft
        return normalized

    @staticmethod
    def _validated_quantity(quantity: int) -> int:
        if quantity <= 0:
            raise AppError(code="validation_error", message="Inventory agent returned a non-positive recommended quantity", status_code=422)
        return quantity

    def _mark_failed(self, agent_run: AgentRun, workflow_run: WorkflowRun | None, message: str) -> None:
        redacted = redact_text(message)
        self.workflow_repository.update_agent_run(agent_run, status="failed", error_message=redacted)
        if workflow_run is not None:
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="failed",
                error_message=redacted,
                completed_at=datetime.now(timezone.utc),
            )
