from __future__ import annotations

import csv
import io
from uuid import UUID, uuid4

from app.agents.pricing.runner import PricingAgentRunner
from app.core.authz import require_any_permission, require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.repositories.pricing_repository import PricingRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.workflow_repository import WorkflowRepository


def serialize_rule(rule) -> dict:
    return {
        "id": str(rule.id),
        "store_id": str(rule.store_id),
        "product_id": str(rule.product_id) if rule.product_id else None,
        "variant_id": str(rule.variant_id) if rule.variant_id else None,
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
        "is_enabled": rule.is_enabled,
        "version_number": rule.version_number,
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
    }


def serialize_recommendation(recommendation) -> dict:
    return {
        "id": str(recommendation.id),
        "pricing_rule_id": str(recommendation.pricing_rule_id) if recommendation.pricing_rule_id else None,
        "reference_input_id": str(recommendation.reference_input_id) if recommendation.reference_input_id else None,
        "product_id": str(recommendation.product_id) if recommendation.product_id else None,
        "variant_id": str(recommendation.variant_id) if recommendation.variant_id else None,
        "workflow_run_id": str(recommendation.workflow_run_id) if recommendation.workflow_run_id else None,
        "agent_run_id": str(recommendation.agent_run_id) if recommendation.agent_run_id else None,
        "approval_request_id": str(recommendation.approval_request_id) if recommendation.approval_request_id else None,
        "current_price": str(recommendation.current_price) if recommendation.current_price is not None else None,
        "recommended_price": str(recommendation.recommended_price) if recommendation.recommended_price is not None else None,
        "cost_snapshot": str(recommendation.cost_snapshot) if recommendation.cost_snapshot is not None else None,
        "margin_floor_snapshot": str(recommendation.margin_floor_snapshot) if recommendation.margin_floor_snapshot is not None else None,
        "price_ceiling_snapshot": str(recommendation.price_ceiling_snapshot) if recommendation.price_ceiling_snapshot is not None else None,
        "reference_price_snapshot": str(recommendation.reference_price_snapshot) if recommendation.reference_price_snapshot is not None else None,
        "applied_strategy": recommendation.applied_strategy,
        "validation_status": recommendation.validation_status,
        "status": recommendation.status,
        "requires_approval": recommendation.requires_approval,
        "explanation_json": recommendation.explanation_json,
        "explanation_summary": recommendation.explanation_summary,
        "confidence_score": float(recommendation.confidence_score) if recommendation.confidence_score is not None else None,
        "needs_human_review": recommendation.needs_human_review,
        "review_reason_code": recommendation.review_reason_code,
        "strategy_inputs_json": recommendation.strategy_inputs_json,
        "created_at": recommendation.created_at,
        "updated_at": recommendation.updated_at,
    }


class PricingModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.sync_repository = SyncRepository(db)
        self.pricing_repository = PricingRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.agent_runner = PricingAgentRunner(db)

    def list_rules(self, user_context: dict, store_id: UUID) -> list[dict]:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.PRICING_READ, Permission.PRICING_MANAGE])
        return [serialize_rule(rule) for rule in self.pricing_repository.list_rules(organization_id, store_id)]

    def create_rule(self, user_context: dict, store_id: UUID, payload) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.PRICING_MANAGE)
        rule = self.pricing_repository.create_rule(
            organization_id=organization_id,
            store_id=store_id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            strategy=payload.strategy,
            delta_amount=self.agent_runner._decimal(payload.delta_amount),
            delta_percentage=self.agent_runner._decimal(payload.delta_percentage),
            markup_percentage=self.agent_runner._decimal(payload.markup_percentage),
            surge_percentage=self.agent_runner._decimal(payload.surge_percentage),
            manual_target_price=self.agent_runner._decimal(payload.manual_target_price),
            cost=self.agent_runner._decimal(payload.cost),
            margin_floor=self.agent_runner._decimal(payload.margin_floor),
            price_ceiling=self.agent_runner._decimal(payload.price_ceiling),
            approval_threshold_percent=self.agent_runner._decimal(payload.approval_threshold_percent),
            force_review=payload.force_review,
            is_enabled=payload.is_enabled,
            version_number=1,
            created_by_user_id=UUID(user_context["user"]["id"]),
            updated_by_user_id=UUID(user_context["user"]["id"]),
        )
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="pricing_rule",
            entity_id=rule.id,
            action_type="created",
            source_type="api",
            outcome="succeeded",
            metadata_json={"strategy": rule.strategy},
        )
        self.db.commit()
        return serialize_rule(rule)

    def get_rule(self, user_context: dict, store_id: UUID, rule_id: UUID) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.PRICING_READ, Permission.PRICING_MANAGE])
        rule = self.pricing_repository.get_rule(organization_id, store_id, rule_id)
        if rule is None:
            raise AppError(code="not_found", message="Pricing rule not found", status_code=404)
        return serialize_rule(rule)

    def update_rule(self, user_context: dict, store_id: UUID, rule_id: UUID, payload) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.PRICING_MANAGE)
        rule = self.pricing_repository.get_rule(organization_id, store_id, rule_id)
        if rule is None:
            raise AppError(code="not_found", message="Pricing rule not found", status_code=404)
        updates = {}
        for field in ("strategy", "force_review", "is_enabled"):
            value = getattr(payload, field)
            if value is not None:
                updates[field] = value
        for field in (
            "delta_amount",
            "delta_percentage",
            "markup_percentage",
            "surge_percentage",
            "manual_target_price",
            "cost",
            "margin_floor",
            "price_ceiling",
            "approval_threshold_percent",
        ):
            value = getattr(payload, field)
            if value is not None:
                updates[field] = self.agent_runner._decimal(value)
        updates["updated_by_user_id"] = UUID(user_context["user"]["id"])
        updates["version_number"] = rule.version_number + 1
        self.pricing_repository.update_rule(rule, **updates)
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="pricing_rule",
            entity_id=rule.id,
            action_type="updated",
            source_type="api",
            outcome="succeeded",
            metadata_json={"version_number": rule.version_number},
        )
        self.db.commit()
        return serialize_rule(rule)

    def delete_rule(self, user_context: dict, store_id: UUID, rule_id: UUID) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.PRICING_MANAGE)
        rule = self.pricing_repository.get_rule(organization_id, store_id, rule_id)
        if rule is None:
            raise AppError(code="not_found", message="Pricing rule not found", status_code=404)
        self.pricing_repository.delete_rule(rule)
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="pricing_rule",
            entity_id=rule.id,
            action_type="deleted",
            source_type="api",
            outcome="succeeded",
            metadata_json={"strategy": rule.strategy},
        )
        self.db.commit()
        return {"deleted": True, "rule_id": str(rule.id)}

    def create_reference_price(self, user_context: dict, store_id: UUID, payload, trace_id: str | None = None) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.PRICING_MANAGE)
        reference_input = self.pricing_repository.create_reference_input(
            organization_id=organization_id,
            store_id=store_id,
            pricing_rule_id=payload.pricing_rule_id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            source_type="manual",
            reference_label=payload.reference_label,
            import_batch_id=None,
            reference_price=self.agent_runner._decimal(payload.reference_price),
            cost_override=self.agent_runner._decimal(payload.cost_override),
            margin_floor_override=self.agent_runner._decimal(payload.margin_floor_override),
            price_ceiling_override=self.agent_runner._decimal(payload.price_ceiling_override),
            payload_json=payload.payload_json,
            created_by_user_id=UUID(user_context["user"]["id"]),
        )
        run_state = self.agent_runner.start_generation(
            organization_id=organization_id,
            store_id=store_id,
            reference_input=reference_input,
            triggered_by_user_id=UUID(user_context["user"]["id"]),
            trace_id=trace_id,
        )
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="price_reference_input",
            entity_id=reference_input.id,
            action_type="created",
            source_type="api",
            outcome="queued",
            metadata_json={"agent_run_id": run_state["agent_run_id"], "source_type": "manual"},
        )
        self.db.commit()
        return {
            "reference_input_id": str(reference_input.id),
            "agent_run_id": run_state["agent_run_id"],
            "workflow_run_id": run_state["workflow_run_id"],
            "status": "queued",
            "trace_id": trace_id,
            "_enqueue_generation": True,
        }

    def import_reference_prices(self, user_context: dict, store_id: UUID, csv_bytes: bytes, trace_id: str | None = None) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.PRICING_MANAGE)
        import_batch_id = uuid4().hex
        reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
        imported_count = 0
        agent_run_ids: list[str] = []
        for row in reader:
            if not any(row.values()):
                continue
            variant_id = UUID(row["variant_id"]) if row.get("variant_id") else None
            product_id = UUID(row["product_id"]) if row.get("product_id") else None
            reference_input = self.pricing_repository.create_reference_input(
                organization_id=organization_id,
                store_id=store_id,
                pricing_rule_id=UUID(row["pricing_rule_id"]) if row.get("pricing_rule_id") else None,
                product_id=product_id,
                variant_id=variant_id,
                source_type="csv_import",
                reference_label=row.get("reference_label"),
                import_batch_id=import_batch_id,
                reference_price=self.agent_runner._decimal(row.get("reference_price")),
                cost_override=self.agent_runner._decimal(row.get("cost_override")),
                margin_floor_override=self.agent_runner._decimal(row.get("margin_floor_override")),
                price_ceiling_override=self.agent_runner._decimal(row.get("price_ceiling_override")),
                payload_json={k: v for k, v in row.items() if v not in (None, "")},
                created_by_user_id=UUID(user_context["user"]["id"]),
            )
            imported_count += 1
            run_state = self.agent_runner.start_generation(
                organization_id=organization_id,
                store_id=store_id,
                reference_input=reference_input,
                triggered_by_user_id=UUID(user_context["user"]["id"]),
                trace_id=trace_id,
            )
            agent_run_ids.append(run_state["agent_run_id"])
        self.db.commit()
        return {
            "import_batch_id": import_batch_id,
            "imported_count": imported_count,
            "recommendation_count": imported_count,
            "blocked_count": 0,
            "queued_count": len(agent_run_ids),
            "trace_id": trace_id,
            "_agent_run_ids": agent_run_ids,
        }

    def simulate(self, user_context: dict, store_id: UUID, payload) -> dict:
        self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.PRICING_READ, Permission.PRICING_MANAGE])
        result = self.agent_runner.simulate(
            payload={
                "pricing_rule": {
                    "strategy": payload.strategy,
                    "delta_amount": payload.delta_amount,
                    "delta_percentage": payload.delta_percentage,
                    "markup_percentage": payload.markup_percentage,
                    "surge_percentage": payload.surge_percentage,
                    "manual_target_price": payload.manual_target_price,
                    "approval_threshold_percent": payload.approval_threshold_percent,
                    "force_review": payload.force_review,
                },
                "product_context": None,
                "variant_context": None,
                "reference_input_context": {
                    "reference_label": "simulation",
                    "reference_price": payload.reference_price,
                    "source_type": "simulation",
                    "payload_json": {},
                },
                "economics_context": {
                    "current_price": payload.current_price,
                    "cost": payload.cost,
                    "margin_floor": payload.margin_floor,
                    "price_ceiling": payload.price_ceiling,
                    "approval_threshold_percent": payload.approval_threshold_percent,
                },
            }
        )
        result["strategy_inputs_json"] = {
            **result["strategy_inputs_json"],
            "strategy": payload.strategy,
            "delta_amount": payload.delta_amount,
            "delta_percentage": payload.delta_percentage,
            "markup_percentage": payload.markup_percentage,
            "surge_percentage": payload.surge_percentage,
            "manual_target_price": payload.manual_target_price,
            "force_review": payload.force_review,
        }
        return result

    def list_recommendations(self, user_context: dict, store_id: UUID, *, status: str | None = None) -> list[dict]:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.PRICING_READ, Permission.PRICING_MANAGE])
        recommendations = self.pricing_repository.list_recommendations(organization_id, store_id, status=status)
        return [serialize_recommendation(recommendation) for recommendation in recommendations]

    def get_recommendation(self, user_context: dict, store_id: UUID, recommendation_id: UUID) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.PRICING_READ, Permission.PRICING_MANAGE])
        recommendation = self.pricing_repository.get_recommendation(organization_id, store_id, recommendation_id)
        if recommendation is None:
            raise AppError(code="not_found", message="Price recommendation not found", status_code=404)
        return serialize_recommendation(recommendation)

    def mark_recommendation_approved(self, recommendation_id: UUID) -> dict:
        recommendation = self.db.get(self._recommendation_model(), recommendation_id)
        if recommendation is None:
            raise AppError(code="not_found", message="Price recommendation not found", status_code=404)
        self.pricing_repository.update_recommendation(recommendation, status="approved")
        self.db.flush()
        return serialize_recommendation(recommendation)

    def mark_recommendation_rejected(self, recommendation_id: UUID) -> dict:
        recommendation = self.db.get(self._recommendation_model(), recommendation_id)
        if recommendation is None:
            raise AppError(code="not_found", message="Price recommendation not found", status_code=404)
        self.pricing_repository.update_recommendation(recommendation, status="rejected")
        self.db.flush()
        return serialize_recommendation(recommendation)

    @staticmethod
    def _recommendation_model():
        from app.repositories.models import PriceRecommendation

        return PriceRecommendation

    def require_store_access(self, user_context: dict, store_id: UUID) -> UUID:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        organization_id = UUID(organization["id"])
        store = self.store_repository.get_store(organization_id, store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return organization_id
