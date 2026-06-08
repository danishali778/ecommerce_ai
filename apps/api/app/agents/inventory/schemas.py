from __future__ import annotations

from pydantic import BaseModel, Field


class InventorySupplierDraftOutput(BaseModel):
    vendor_name: str | None = None
    recipient_email: str | None = None
    subject: str | None = None
    body: str | None = None


class InventoryAgentOutput(BaseModel):
    recommended_quantity: int = Field(ge=1)
    urgency: str = Field(pattern="^(low|medium|high|critical)$")
    rationale_summary: str = Field(min_length=1)
    rationale_json: dict = Field(default_factory=dict)
    confidence_score: float = Field(ge=0.0, le=1.0)
    needs_human_review: bool = False
    review_reason_code: str | None = None
    supplier_draft: InventorySupplierDraftOutput | None = None
