from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from app.agents.pricing.prompts import build_pricing_recommendation_prompt
from app.agents.pricing.schemas import PricingAgentOutput
from app.core.errors import AppError
from app.core.redaction import redact_text
from app.llm.provider import LLMProvider
from app.modules.workflows.events import emit_workflow_event
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.models import AgentRun, PriceReferenceInput, PriceRecommendation, PricingRule, Product, ProductVariant, WorkflowRun
from app.repositories.pricing_repository import PricingRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workflow_repository import WorkflowRepository


SAFE_CONTEXT_ROLES = ["Owner", "Admin", "Manager"]


class PricingAgentRunner:
    def __init__(self, db) -> None:
        self.db = db
        self.pricing_repository = PricingRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.approval_repository = ApprovalRepository(db)
        self.user_repository = UserRepository(db)
        self.sync_repository = SyncRepository(db)
        self.llm_provider = LLMProvider()

    def start_generation(
        self,
        *,
        organization_id: UUID,
        store_id: UUID,
        reference_input: PriceReferenceInput,
        triggered_by_user_id: UUID | None,
        trace_id: str | None = None,
    ) -> dict:
        workflow = self.workflow_repository.ensure_system_workflow(
            key="pricing_recommendation_generated",
            name="Pricing Recommendation Generated",
            phase_scope="p2",
            trigger_type="pricing.recommendation.created",
            action_type="pricing_recommendation_saved",
        )
        workflow_run = self.workflow_repository.create_workflow_run(
            organization_id=organization_id,
            store_id=store_id,
            workflow_id=workflow.id,
            trigger_type="pricing.recommendation.created",
            trigger_entity_type="price_reference_input",
            trigger_entity_id=reference_input.id,
            status="queued",
            trace_id=trace_id,
            input_payload={"reference_input_id": str(reference_input.id)},
            output_payload={},
        )
        agent_run = self.workflow_repository.create_agent_run(
            organization_id=organization_id,
            store_id=store_id,
            agent_type="pricing_recommendation",
            user_id=triggered_by_user_id,
            workflow_run_id=workflow_run.id,
            input_summary=f"Generate pricing recommendation for reference input {reference_input.id}",
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
        reference_input_id = (workflow_run.input_payload or {}).get("reference_input_id") if workflow_run else None
        reference_input = self.db.get(PriceReferenceInput, UUID(reference_input_id)) if reference_input_id else None
        if workflow_run is None or reference_input is None:
            self._mark_failed(agent_run, workflow_run, "Pricing agent context is incomplete")
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
            recommendation = self.persist_recommendation(
                reference_input=reference_input,
                workflow_run=workflow_run,
                agent_run=agent_run,
                trace_id=trace_id or agent_run.trace_id,
            )
            self.workflow_repository.update_agent_run(
                agent_run,
                status="succeeded",
                trace_id=trace_id or agent_run.trace_id,
                retrieved_context_summary=f"reference_input={reference_input.id} product={reference_input.product_id} variant={reference_input.variant_id}",
                output_summary=redact_text(recommendation.explanation_summary or ""),
            )
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="succeeded",
                trace_id=trace_id or workflow_run.trace_id,
                output_payload={
                    "price_recommendation_id": str(recommendation.id),
                    "agent_run_id": str(agent_run.id),
                },
                completed_at=datetime.now(timezone.utc),
            )
            self.db.commit()
            return {
                "price_recommendation_id": str(recommendation.id),
                "workflow_run_id": str(workflow_run.id),
                "agent_run_id": str(agent_run.id),
                "status": recommendation.status,
            }
        except Exception as exc:  # noqa: BLE001
            self._mark_failed(agent_run, workflow_run, str(exc))
            self.db.commit()
            raise

    def simulate(self, *, payload: dict) -> dict:
        output = self._generate_output(
            pricing_rule=payload.get("pricing_rule"),
            product_context=payload.get("product_context"),
            variant_context=payload.get("variant_context"),
            reference_input_context=payload["reference_input_context"],
            economics_context=payload["economics_context"],
        )
        validated = self._validated_output(
            output=output,
            current_price=self._decimal(payload["economics_context"].get("current_price")),
            reference_price=self._decimal(payload["reference_input_context"].get("reference_price")),
            cost=self._decimal(payload["economics_context"].get("cost")),
            margin_floor=self._decimal(payload["economics_context"].get("margin_floor")),
            price_ceiling=self._decimal(payload["economics_context"].get("price_ceiling")),
            approval_threshold_percent=self._decimal(payload["economics_context"].get("approval_threshold_percent")),
        )
        return validated

    def persist_recommendation(self, *, reference_input: PriceReferenceInput, workflow_run: WorkflowRun, agent_run: AgentRun, trace_id: str | None) -> PriceRecommendation:
        variant = self.sync_repository.get_variant(reference_input.organization_id, reference_input.store_id, reference_input.variant_id) if reference_input.variant_id else None
        product = self.sync_repository.get_product(reference_input.organization_id, reference_input.store_id, reference_input.product_id) if reference_input.product_id else None
        if product is None and variant is not None:
            product = self.sync_repository.get_product(reference_input.organization_id, reference_input.store_id, variant.product_id)
        rule = self.pricing_repository.get_rule(reference_input.organization_id, reference_input.store_id, reference_input.pricing_rule_id) if reference_input.pricing_rule_id else None
        if rule is None:
            rule = self.pricing_repository.find_rule_for_target(
                reference_input.organization_id,
                reference_input.store_id,
                product_id=reference_input.product_id or (variant.product_id if variant else None),
                variant_id=reference_input.variant_id,
            )
        output = self._generate_output(
            pricing_rule=self._serialize_rule(rule),
            product_context=self._serialize_product(product),
            variant_context=self._serialize_variant(variant),
            reference_input_context={
                "id": str(reference_input.id),
                "reference_label": reference_input.reference_label,
                "reference_price": str(reference_input.reference_price) if reference_input.reference_price is not None else None,
                "source_type": reference_input.source_type,
                "payload_json": reference_input.payload_json,
            },
            economics_context={
                "current_price": str(variant.price) if variant and variant.price is not None else None,
                "cost": str(reference_input.cost_override or (rule.cost if rule else (variant.cost if variant else None))) if (reference_input.cost_override or (rule.cost if rule else (variant.cost if variant else None))) is not None else None,
                "margin_floor": str(reference_input.margin_floor_override or (rule.margin_floor if rule else (variant.margin_floor if variant else None))) if (reference_input.margin_floor_override or (rule.margin_floor if rule else (variant.margin_floor if variant else None))) is not None else None,
                "price_ceiling": str(reference_input.price_ceiling_override or (rule.price_ceiling if rule else (variant.price_ceiling if variant else None))) if (reference_input.price_ceiling_override or (rule.price_ceiling if rule else (variant.price_ceiling if variant else None))) is not None else None,
                "approval_threshold_percent": str(rule.approval_threshold_percent) if rule and rule.approval_threshold_percent is not None else None,
            },
        )
        cost = reference_input.cost_override or (rule.cost if rule else (variant.cost if variant else None))
        margin_floor = reference_input.margin_floor_override or (rule.margin_floor if rule else (variant.margin_floor if variant else None))
        price_ceiling = reference_input.price_ceiling_override or (rule.price_ceiling if rule else (variant.price_ceiling if variant else None))
        validated = self._validated_output(
            output=output,
            current_price=variant.price if variant else None,
            reference_price=reference_input.reference_price,
            cost=cost,
            margin_floor=margin_floor,
            price_ceiling=price_ceiling,
            approval_threshold_percent=rule.approval_threshold_percent if rule else None,
        )
        open_recommendations = self.pricing_repository.list_recommendations(
            reference_input.organization_id,
            reference_input.store_id,
            status=None,
            variant_id=reference_input.variant_id,
            product_id=reference_input.product_id or (variant.product_id if variant else None),
        )
        for stale in open_recommendations:
            if stale.status in {"draft", "pending_approval"}:
                self.pricing_repository.update_recommendation(stale, status="superseded")
        recommendation = self.pricing_repository.create_recommendation(
            organization_id=reference_input.organization_id,
            store_id=reference_input.store_id,
            pricing_rule_id=rule.id if rule else None,
            reference_input_id=reference_input.id,
            product_id=reference_input.product_id or (variant.product_id if variant else None),
            variant_id=reference_input.variant_id,
            workflow_run_id=workflow_run.id,
            agent_run_id=agent_run.id,
            approval_request_id=None,
            superseded_by_recommendation_id=None,
            current_price=variant.price if variant else None,
            recommended_price=self._decimal(validated["recommended_price"]),
            cost_snapshot=cost,
            margin_floor_snapshot=margin_floor,
            price_ceiling_snapshot=price_ceiling,
            reference_price_snapshot=reference_input.reference_price,
            applied_strategy=validated["applied_strategy"],
            validation_status=validated["validation_status"],
            status="pending_approval" if validated["requires_approval"] else ("draft" if validated["validation_status"] == "valid" else "draft"),
            requires_approval=validated["requires_approval"],
            explanation_json=validated["explanation_json"],
            explanation_summary=validated["rationale_summary"],
            strategy_inputs_json=validated["strategy_inputs_json"],
            confidence_score=Decimal(str(validated["confidence_score"])) if validated["confidence_score"] is not None else None,
            needs_human_review=validated["needs_human_review"],
            review_reason_code=validated["review_reason_code"],
            created_by_user_id=agent_run.user_id,
        )
        self.workflow_repository.create_audit_event(
            organization_id=reference_input.organization_id,
            store_id=reference_input.store_id,
            user_id=agent_run.user_id,
            entity_type="price_recommendation",
            entity_id=recommendation.id,
            action_type="agent_generated",
            source_type="agent",
            outcome="blocked" if validated["validation_status"] != "valid" else ("review_required" if validated["requires_approval"] else "succeeded"),
            metadata_json={
                "agent_type": agent_run.agent_type,
                "validation_status": validated["validation_status"],
                "requires_approval": validated["requires_approval"],
                "confidence_score": validated["confidence_score"],
            },
        )
        if validated["requires_approval"]:
            approval = self._create_pricing_approval(reference_input.organization_id, reference_input.store_id, recommendation, agent_run.user_id)
            self.pricing_repository.update_recommendation(recommendation, approval_request_id=approval.id, status="pending_approval")
            emit_workflow_event(
                organization_id=reference_input.organization_id,
                store_id=reference_input.store_id,
                trigger_type="approval.pending",
                entity_type="approval_request",
                entity_id=approval.id,
                trace_id=trace_id or workflow_run.trace_id,
                payload={
                    "approval_id": str(approval.id),
                    "approval.action_type": approval.action_type,
                    "approval.entity_type": approval.entity_type,
                    "action_type": approval.action_type,
                    "entity_type": approval.entity_type,
                },
            )
        emit_workflow_event(
            organization_id=reference_input.organization_id,
            store_id=reference_input.store_id,
            trigger_type="pricing.recommendation.created",
            entity_type="price_recommendation",
            entity_id=recommendation.id,
            trace_id=trace_id or workflow_run.trace_id,
            payload={
                "recommendation_id": str(recommendation.id),
                "product_id": str(recommendation.product_id) if recommendation.product_id else None,
                "variant_id": str(recommendation.variant_id) if recommendation.variant_id else None,
                "pricing.recommended_price": str(recommendation.recommended_price) if recommendation.recommended_price is not None else None,
                "pricing.validation_status": recommendation.validation_status,
                "pricing.requires_approval": recommendation.requires_approval,
                "recommended_price": str(recommendation.recommended_price) if recommendation.recommended_price is not None else None,
                "validation_status": recommendation.validation_status,
                "requires_approval": recommendation.requires_approval,
            },
        )
        self.workflow_repository.update_workflow_run(workflow_run, trace_id=trace_id or workflow_run.trace_id)
        return recommendation

    def _generate_output(
        self,
        *,
        pricing_rule: dict | None,
        product_context: dict | None,
        variant_context: dict | None,
        reference_input_context: dict,
        economics_context: dict,
    ) -> PricingAgentOutput:
        def generate_node(state: dict) -> dict:
            prompt = build_pricing_recommendation_prompt(
                pricing_rule=state["pricing_rule"],
                product_context=state["product_context"],
                variant_context=state["variant_context"],
                reference_input_context=state["reference_input_context"],
                economics_context=state["economics_context"],
            )
            raw = self.llm_provider.generate_structured_json(prompt)
            output = PricingAgentOutput.model_validate(raw)
            return {"result": output}

        graph = StateGraph(dict)
        graph.add_node("generate", generate_node)
        graph.add_edge(START, "generate")
        graph.add_edge("generate", END)
        result = graph.compile().invoke(
            {
                "pricing_rule": pricing_rule,
                "product_context": product_context,
                "variant_context": variant_context,
                "reference_input_context": reference_input_context,
                "economics_context": economics_context,
            }
        )
        return result["result"]

    def _validated_output(
        self,
        *,
        output: PricingAgentOutput,
        current_price: Decimal | None,
        reference_price: Decimal | None,
        cost: Decimal | None,
        margin_floor: Decimal | None,
        price_ceiling: Decimal | None,
        approval_threshold_percent: Decimal | None,
    ) -> dict:
        recommended_price = self._decimal(output.recommended_price)
        validation_status = output.validation_status
        reasons = list(output.explanation_json.get("reasons", [])) if isinstance(output.explanation_json, dict) else []
        requires_approval = output.requires_approval
        review_reason_code = output.review_reason_code
        needs_human_review = output.needs_human_review

        if cost is None or margin_floor is None:
            validation_status = "manual_review"
            requires_approval = True
            needs_human_review = True
            review_reason_code = review_reason_code or "missing_economics"
            reasons.append("missing_economics")

        if recommended_price is not None and margin_floor is not None and recommended_price < margin_floor:
            validation_status = "blocked"
            recommended_price = None
            reasons.append("below_margin_floor")
        if recommended_price is not None and price_ceiling is not None and recommended_price > price_ceiling:
            validation_status = "blocked"
            recommended_price = None
            reasons.append("above_price_ceiling")
        if recommended_price is None and validation_status == "valid":
            validation_status = "blocked"
            reasons.append("missing_recommended_price")
        if recommended_price is not None and current_price is not None and approval_threshold_percent is not None and current_price != 0:
            delta_percent = abs(((recommended_price - current_price) / current_price) * Decimal("100"))
            if delta_percent >= approval_threshold_percent:
                requires_approval = True
                reasons.append("approval_threshold_exceeded")
        if validation_status != "valid":
            needs_human_review = True
            review_reason_code = review_reason_code or ("blocked_recommendation" if validation_status == "blocked" else "manual_review_required")

        explanation_json = dict(output.explanation_json)
        explanation_json["reasons"] = reasons
        explanation_json["safe_to_execute"] = validation_status == "valid" and not requires_approval
        explanation_json["reference_price"] = str(reference_price) if reference_price is not None else None
        explanation_json["cost"] = str(cost) if cost is not None else None
        explanation_json["margin_floor"] = str(margin_floor) if margin_floor is not None else None
        explanation_json["price_ceiling"] = str(price_ceiling) if price_ceiling is not None else None
        return {
            "recommended_price": str(recommended_price.quantize(Decimal("0.0001"))) if recommended_price is not None else None,
            "validation_status": validation_status,
            "requires_approval": requires_approval,
            "applied_strategy": output.applied_strategy,
            "rationale_summary": output.rationale_summary,
            "explanation_json": explanation_json,
            "strategy_inputs_json": output.strategy_inputs_json,
            "confidence_score": output.confidence_score,
            "needs_human_review": needs_human_review,
            "review_reason_code": review_reason_code,
        }

    def _create_pricing_approval(self, organization_id: UUID, store_id: UUID, recommendation: PriceRecommendation, requested_by_user_id: UUID | None):
        snapshot = {
            "recommendation_id": str(recommendation.id),
            "proposed_price": str(recommendation.recommended_price) if recommendation.recommended_price is not None else None,
            "strategy": recommendation.applied_strategy,
            "inputs": recommendation.strategy_inputs_json,
            "validation_status": recommendation.validation_status,
            "explanation": recommendation.explanation_json,
        }
        approval = self.approval_repository.create_approval(
            organization_id=organization_id,
            store_id=store_id,
            action_type="pricing_recommendation_approval",
            entity_type="price_recommendation",
            entity_id=recommendation.id,
            workflow_run_id=recommendation.workflow_run_id,
            agent_run_id=recommendation.agent_run_id,
            proposed_action_json=snapshot,
            source_snapshot_hash=self._snapshot_hash(snapshot),
            source_snapshot_created_at=datetime.now(timezone.utc),
            reasoning="Pricing recommendation exceeded safe auto-accept thresholds and requires operator review.",
            status="pending",
            review_notes=None,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            execution_status=None,
            execution_error=None,
            idempotency_key=f"pricing-approval:{recommendation.id}",
            requested_by_user_id=requested_by_user_id,
            reviewed_by_user_id=None,
            reviewed_at=None,
            last_execution_attempt_at=None,
            retry_count=0,
        )
        for user in self.user_repository.list_users_with_any_role(organization_id, SAFE_CONTEXT_ROLES):
            self.workflow_repository.create_notification(
                organization_id=organization_id,
                store_id=store_id,
                user_id=user.id,
                type="pricing_approval_pending",
                channel="in_app",
                title="Pricing recommendation requires review",
                body="A pricing recommendation is pending approval.",
                payload_json={"approval_id": str(approval.id), "recommendation_id": str(recommendation.id)},
                status="unread",
            )
        return approval

    @staticmethod
    def _snapshot_hash(payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    @staticmethod
    def _serialize_rule(rule: PricingRule | None) -> dict | None:
        if rule is None:
            return None
        return {
            "id": str(rule.id),
            "strategy": rule.strategy,
            "delta_amount": str(rule.delta_amount) if rule.delta_amount is not None else None,
            "delta_percentage": str(rule.delta_percentage) if rule.delta_percentage is not None else None,
            "markup_percentage": str(rule.markup_percentage) if rule.markup_percentage is not None else None,
            "surge_percentage": str(rule.surge_percentage) if rule.surge_percentage is not None else None,
            "manual_target_price": str(rule.manual_target_price) if rule.manual_target_price is not None else None,
            "cost": str(rule.cost) if rule.cost is not None else None,
            "margin_floor": str(rule.margin_floor) if rule.margin_floor is not None else None,
            "price_ceiling": str(rule.price_ceiling) if rule.price_ceiling is not None else None,
            "approval_threshold_percent": str(rule.approval_threshold_percent) if rule.approval_threshold_percent is not None else None,
            "force_review": rule.force_review,
        }

    @staticmethod
    def _serialize_product(product: Product | None) -> dict | None:
        if product is None:
            return None
        return {
            "id": str(product.id),
            "title": product.title,
            "vendor": product.vendor,
            "category": product.category,
            "tags": product.tags,
        }

    @staticmethod
    def _serialize_variant(variant: ProductVariant | None) -> dict | None:
        if variant is None:
            return None
        return {
            "id": str(variant.id),
            "sku": variant.sku,
            "title": variant.title,
            "price": str(variant.price) if variant.price is not None else None,
            "cost": str(variant.cost) if variant.cost is not None else None,
            "margin_floor": str(variant.margin_floor) if variant.margin_floor is not None else None,
            "price_ceiling": str(variant.price_ceiling) if variant.price_ceiling is not None else None,
        }

    @staticmethod
    def _decimal(value) -> Decimal | None:
        if value in (None, ""):
            return None
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise AppError(code="validation_error", message=f"Invalid decimal value: {value}", status_code=422) from exc

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
