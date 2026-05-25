from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.schemas.common import (
    CustomerSummary,
    IntegrationSummary,
    OrderSummary,
    ProductDetail,
    ProductDraftSummary,
    ProductSummary,
    StoreSummary,
    SyncRunSummary,
)


class StoreCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    platform: str = "shopify"
    domain: str = Field(min_length=3, max_length=255)
    currency: str | None = None
    timezone: str | None = None


class InstallURLRequest(BaseModel):
    redirect_uri: str


class SyncRunCreateRequest(BaseModel):
    mode: str = "manual_full"


class DraftGenerateRequest(BaseModel):
    generation_targets: list[str] = Field(default_factory=lambda: ["description", "seo", "tags"])
    tone: str = "clear_and_premium"
    constraints: dict = Field(default_factory=dict)


class DraftUpdateRequest(BaseModel):
    generated_title: str | None = None
    generated_description: str | None = None
    generated_tags: list[str] | None = None
    generated_seo_title: str | None = None
    generated_seo_description: str | None = None


class SubmitApprovalRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class StoreResponse(StoreSummary):
    pass


class InstallURLResponse(BaseModel):
    install_url: str
    state: str


class DraftGenerationAcceptedResponse(BaseModel):
    agent_run_id: UUID
    workflow_run_id: UUID
    status: str


class DraftApprovalSubmissionResponse(BaseModel):
    approval_id: UUID
    approval_status: str
    draft_status: str


class DashboardSummaryResponse(BaseModel):
    latest_sync_status: str | None = None
    latest_sync_completed_at: str | None = None
    product_count: int
    order_count: int
    customer_count: int
    low_inventory_count: int
    pending_approval_count: int
    recent_workflow_failures: int
    recent_agent_runs: int
