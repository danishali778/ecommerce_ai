from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


PRICING_STRATEGIES = ("MATCH", "BEAT", "COST_PLUS", "SURGE", "MANUAL_REVIEW")


class PricingRuleCreateRequest(BaseModel):
    product_id: UUID | None = None
    variant_id: UUID | None = None
    strategy: str = Field(pattern="^(MATCH|BEAT|COST_PLUS|SURGE|MANUAL_REVIEW)$")
    delta_amount: str | None = None
    delta_percentage: str | None = None
    markup_percentage: str | None = None
    surge_percentage: str | None = None
    manual_target_price: str | None = None
    cost: str | None = None
    margin_floor: str | None = None
    price_ceiling: str | None = None
    approval_threshold_percent: str | None = None
    force_review: bool = False
    is_enabled: bool = True

    @model_validator(mode="after")
    def validate_target(self) -> "PricingRuleCreateRequest":
        if not self.product_id and not self.variant_id:
            raise ValueError("product_id or variant_id is required")
        return self


class PricingRuleUpdateRequest(BaseModel):
    strategy: str | None = Field(default=None, pattern="^(MATCH|BEAT|COST_PLUS|SURGE|MANUAL_REVIEW)$")
    delta_amount: str | None = None
    delta_percentage: str | None = None
    markup_percentage: str | None = None
    surge_percentage: str | None = None
    manual_target_price: str | None = None
    cost: str | None = None
    margin_floor: str | None = None
    price_ceiling: str | None = None
    approval_threshold_percent: str | None = None
    force_review: bool | None = None
    is_enabled: bool | None = None


class PricingRuleResponse(BaseModel):
    id: UUID
    store_id: UUID
    product_id: UUID | None = None
    variant_id: UUID | None = None
    strategy: str
    delta_amount: str | None = None
    delta_percentage: str | None = None
    markup_percentage: str | None = None
    surge_percentage: str | None = None
    manual_target_price: str | None = None
    cost: str | None = None
    margin_floor: str | None = None
    price_ceiling: str | None = None
    approval_threshold_percent: str | None = None
    force_review: bool
    is_enabled: bool
    version_number: int
    created_at: datetime
    updated_at: datetime


class ReferencePriceCreateRequest(BaseModel):
    pricing_rule_id: UUID | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    reference_label: str | None = None
    reference_price: str | None = None
    cost_override: str | None = None
    margin_floor_override: str | None = None
    price_ceiling_override: str | None = None
    payload_json: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_target(self) -> "ReferencePriceCreateRequest":
        if not self.product_id and not self.variant_id:
            raise ValueError("product_id or variant_id is required")
        return self


class ReferencePriceImportResponse(BaseModel):
    import_batch_id: str
    imported_count: int
    recommendation_count: int
    blocked_count: int
    queued_count: int | None = None


class PricingSimulationRequest(BaseModel):
    strategy: str = Field(pattern="^(MATCH|BEAT|COST_PLUS|SURGE|MANUAL_REVIEW)$")
    current_price: str | None = None
    reference_price: str | None = None
    cost: str | None = None
    margin_floor: str | None = None
    price_ceiling: str | None = None
    delta_amount: str | None = None
    delta_percentage: str | None = None
    markup_percentage: str | None = None
    surge_percentage: str | None = None
    manual_target_price: str | None = None
    approval_threshold_percent: str | None = None
    force_review: bool = False


class PricingSimulationResponse(BaseModel):
    recommended_price: str | None = None
    validation_status: str
    requires_approval: bool
    explanation_json: dict
    rationale_summary: str | None = None
    confidence_score: float | None = None
    needs_human_review: bool = False
    review_reason_code: str | None = None
    strategy_inputs_json: dict


class PriceRecommendationResponse(BaseModel):
    id: UUID
    pricing_rule_id: UUID | None = None
    reference_input_id: UUID | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    workflow_run_id: UUID | None = None
    agent_run_id: UUID | None = None
    approval_request_id: UUID | None = None
    current_price: str | None = None
    recommended_price: str | None = None
    cost_snapshot: str | None = None
    margin_floor_snapshot: str | None = None
    price_ceiling_snapshot: str | None = None
    reference_price_snapshot: str | None = None
    applied_strategy: str
    validation_status: str
    status: str
    requires_approval: bool
    explanation_json: dict
    explanation_summary: str | None = None
    confidence_score: float | None = None
    needs_human_review: bool = False
    review_reason_code: str | None = None
    strategy_inputs_json: dict
    created_at: datetime
    updated_at: datetime
