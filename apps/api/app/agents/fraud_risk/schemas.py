from __future__ import annotations

from pydantic import BaseModel, Field


class FraudRiskAgentOutput(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_status: str = Field(pattern="^(low_risk|medium_risk|high_risk)$")
    reason_codes: list[str] = Field(default_factory=list)
    explanation_summary: str = Field(min_length=1)
    evidence_json: dict = Field(default_factory=dict)
    confidence_score: float = Field(ge=0.0, le=1.0)
    needs_human_review: bool = False
    review_reason_code: str | None = None
    recommended_decision: str | None = Field(default=None, pattern="^(approved|held|rejected)$")
