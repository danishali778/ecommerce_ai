from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class OrderRiskScoreResponse(BaseModel):
    order_id: UUID
    risk_score: int
    risk_status: str


class RiskReviewDecisionRequest(BaseModel):
    decision: str = Field(min_length=1, max_length=50)
    decision_notes: str | None = None


class RiskReviewResponse(BaseModel):
    id: UUID
    order_id: UUID
    risk_score: int
    risk_status: str
    reason_codes_json: list[str] = Field(default_factory=list)
    decision: str | None = None
    decision_notes: str | None = None
    reviewed_by_user_id: UUID | None = None
    reviewed_at: str | None = None
    created_at: str
    updated_at: str
