from __future__ import annotations

from pydantic import BaseModel, Field


class PricingAgentOutput(BaseModel):
    recommended_price: str | None = None
    validation_status: str = Field(pattern="^(valid|blocked|manual_review)$")
    requires_approval: bool
    applied_strategy: str
    rationale_summary: str = Field(min_length=1)
    explanation_json: dict = Field(default_factory=dict)
    strategy_inputs_json: dict = Field(default_factory=dict)
    confidence_score: float = Field(ge=0.0, le=1.0)
    needs_human_review: bool = False
    review_reason_code: str | None = None
