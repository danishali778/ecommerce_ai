from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class InventoryAlertResponse(BaseModel):
    id: UUID
    product_id: UUID
    variant_id: UUID
    threshold_value: int
    current_quantity: int
    status: str
    resolved_at: str | None = None
    created_at: str
    updated_at: str


class SupplierReorderDraftUpsertRequest(BaseModel):
    vendor_name: str | None = Field(default=None, max_length=255)
    recipient_email: str | None = Field(default=None, max_length=255)
    subject: str | None = Field(default=None, max_length=255)
    body: str | None = None
    status: str | None = Field(default=None, max_length=50)


class SupplierReorderDraftResponse(BaseModel):
    id: UUID
    vendor_name: str
    recipient_email: str | None = None
    subject: str
    body: str
    status: str
    created_by_user_id: UUID | None = None
    created_at: str
    updated_at: str


class ReorderSuggestionResponse(BaseModel):
    id: UUID
    inventory_alert_id: UUID
    product_id: UUID
    variant_id: UUID | None = None
    agent_run_id: UUID | None = None
    recommended_quantity: int
    current_quantity: int
    threshold_value: int
    rationale_json: dict = Field(default_factory=dict)
    rationale_summary: str | None = None
    urgency: str | None = None
    confidence_score: float | None = None
    needs_human_review: bool = False
    review_reason_code: str | None = None
    status: str
    created_at: str
    updated_at: str
    supplier_draft: SupplierReorderDraftResponse | None = None
