from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from app.agents.fraud_risk.prompts import build_fraud_risk_prompt
from app.agents.fraud_risk.schemas import FraudRiskAgentOutput
from app.core.errors import AppError
from app.core.redaction import redact_text
from app.llm.provider import LLMProvider
from app.repositories.fraud_repository import FraudRepository
from app.repositories.models import AgentRun, Order, RiskReview, WorkflowRun
from app.repositories.sync_repository import SyncRepository
from app.repositories.workflow_repository import WorkflowRepository


class FraudRiskAgentRunner:
    def __init__(self, db) -> None:
        self.db = db
        self.fraud_repository = FraudRepository(db)
        self.sync_repository = SyncRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.llm_provider = LLMProvider()

    def start_generation(
        self,
        *,
        organization_id: UUID,
        store_id: UUID,
        order: Order,
        triggered_by_user_id: UUID | None,
        trace_id: str | None = None,
    ) -> dict:
        workflow = self.workflow_repository.ensure_system_workflow(
            key="fraud_risk_assessed",
            name="Fraud Risk Assessed",
            phase_scope="p1",
            trigger_type="order.imported",
            action_type="fraud_risk_saved",
        )
        workflow_run = self.workflow_repository.create_workflow_run(
            organization_id=organization_id,
            store_id=store_id,
            workflow_id=workflow.id,
            trigger_type="order.imported",
            trigger_entity_type="order",
            trigger_entity_id=order.id,
            status="queued",
            trace_id=trace_id,
            input_payload={"order_id": str(order.id)},
            output_payload={},
        )
        agent_run = self.workflow_repository.create_agent_run(
            organization_id=organization_id,
            store_id=store_id,
            agent_type="fraud_risk",
            user_id=triggered_by_user_id,
            workflow_run_id=workflow_run.id,
            input_summary=f"Assess fraud risk for order {order.id}",
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
        order_id = (workflow_run.input_payload or {}).get("order_id") if workflow_run else None
        order = self.db.get(Order, UUID(order_id)) if order_id else None
        if workflow_run is None or order is None:
            self._mark_failed(agent_run, workflow_run, "Fraud agent context is incomplete")
            self.db.commit()
            return None
        customer = self.sync_repository.get_customer(order.organization_id, order.store_id, order.customer_id) if order.customer_id else None
        existing_review = self.fraud_repository.get_pending_review_for_order(order.id)
        try:
            now = datetime.now(timezone.utc)
            self.workflow_repository.update_agent_run(agent_run, status="running", trace_id=trace_id or agent_run.trace_id)
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="running",
                trace_id=trace_id or workflow_run.trace_id,
                started_at=workflow_run.started_at or now,
            )
            output = self._generate_output(order=order, customer=customer, existing_review=existing_review)
            risk_status = self._validated_risk_status(output.risk_status)
            recommended_decision = output.recommended_decision
            if recommended_decision not in {None, "approved", "held", "rejected"}:
                raise AppError(code="validation_error", message="Fraud agent returned an unsupported recommendation", status_code=422)
            review_reason_code = output.review_reason_code
            if output.confidence_score < 0.65 and not review_reason_code:
                review_reason_code = "low_confidence"
            if output.needs_human_review and not review_reason_code:
                review_reason_code = "fraud_review_required"

            order.risk_score = output.risk_score
            order.risk_status = risk_status
            review = existing_review
            should_create_review = risk_status == "high_risk" or output.needs_human_review or output.risk_score >= 60
            if should_create_review:
                values = {
                    "agent_run_id": agent_run.id,
                    "risk_score": output.risk_score,
                    "risk_status": "pending_review",
                    "reason_codes_json": output.reason_codes,
                    "explanation_json": output.evidence_json,
                    "explanation_summary": output.explanation_summary,
                    "confidence_score": Decimal(str(output.confidence_score)),
                    "needs_human_review": output.needs_human_review,
                    "review_reason_code": review_reason_code,
                    "recommended_decision": recommended_decision,
                }
                if review is None:
                    review = self.fraud_repository.create_review(
                        organization_id=order.organization_id,
                        store_id=order.store_id,
                        order_id=order.id,
                        decision=None,
                        decision_notes=None,
                        reviewed_by_user_id=None,
                        reviewed_at=None,
                        **values,
                    )
                else:
                    self.fraud_repository.update_review(review, **values)

            self.workflow_repository.create_audit_event(
                organization_id=order.organization_id,
                store_id=order.store_id,
                user_id=agent_run.user_id,
                entity_type="risk_review" if review else "order",
                entity_id=review.id if review else order.id,
                action_type="agent_assessed",
                source_type="agent",
                outcome="review_required" if should_create_review else "succeeded",
                metadata_json={
                    "agent_type": agent_run.agent_type,
                    "risk_score": output.risk_score,
                    "risk_status": risk_status,
                    "confidence_score": output.confidence_score,
                },
            )
            self.workflow_repository.update_agent_run(
                agent_run,
                status="succeeded",
                trace_id=trace_id or agent_run.trace_id,
                retrieved_context_summary=f"order={order.id} customer={order.customer_id}",
                output_summary=redact_text(output.explanation_summary),
            )
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="succeeded",
                trace_id=trace_id or workflow_run.trace_id,
                output_payload={
                    "order_id": str(order.id),
                    "risk_review_id": str(review.id) if review else None,
                    "agent_run_id": str(agent_run.id),
                },
                completed_at=datetime.now(timezone.utc),
            )
            self.db.commit()
            return {
                "order_id": str(order.id),
                "risk_review_id": str(review.id) if review else None,
                "workflow_run_id": str(workflow_run.id),
                "agent_run_id": str(agent_run.id),
                "risk_status": risk_status,
            }
        except Exception as exc:  # noqa: BLE001
            self._mark_failed(agent_run, workflow_run, str(exc))
            self.db.commit()
            raise

    def _generate_output(self, *, order: Order, customer, existing_review: RiskReview | None) -> FraudRiskAgentOutput:
        def generate_node(state: dict) -> dict:
            prompt = build_fraud_risk_prompt(
                order_context=state["order_context"],
                customer_context=state["customer_context"],
                existing_review=state["existing_review"],
            )
            raw = self.llm_provider.generate_structured_json(prompt)
            output = FraudRiskAgentOutput.model_validate(raw)
            return {"result": output}

        graph = StateGraph(dict)
        graph.add_node("generate", generate_node)
        graph.add_edge(START, "generate")
        graph.add_edge("generate", END)
        result = graph.compile().invoke(
            {
                "order_context": {
                    "id": str(order.id),
                    "external_order_id": order.external_order_id,
                    "total": str(order.total),
                    "currency": order.currency,
                    "payment_status": order.payment_status,
                    "fulfillment_status": order.fulfillment_status,
                    "payment_attempt_count": order.payment_attempt_count,
                    "billing_country": order.billing_country,
                    "shipping_country": order.shipping_country,
                    "billing_postal_code": order.billing_postal_code,
                    "shipping_postal_code": order.shipping_postal_code,
                },
                "customer_context": {
                    "id": str(customer.id),
                    "email": customer.email,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "total_orders": customer.total_orders,
                }
                if customer
                else None,
                "existing_review": {
                    "id": str(existing_review.id),
                    "risk_score": existing_review.risk_score,
                    "reason_codes": existing_review.reason_codes_json,
                    "decision": existing_review.decision,
                }
                if existing_review
                else None,
            }
        )
        return result["result"]

    @staticmethod
    def _validated_risk_status(risk_status: str) -> str:
        if risk_status not in {"low_risk", "medium_risk", "high_risk"}:
            raise AppError(code="validation_error", message="Fraud agent returned an unsupported risk status", status_code=422)
        return risk_status

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
