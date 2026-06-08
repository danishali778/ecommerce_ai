from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    request_id: str | None = None
    timestamp: str
    next_cursor: str | None = None
    count: int | None = None


DataT = TypeVar("DataT")


class SuccessEnvelope(BaseModel, Generic[DataT]):
    data: DataT
    meta: PaginationMeta


class UserSummary(ORMModel):
    id: UUID
    email: str
    full_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class RoleSummary(BaseModel):
    name: str
    description: str
    permissions: list[str]


class IntegrationSummary(BaseModel):
    provider: str
    scopes: list[str]
    status: str
    last_successful_sync_at: str | None = None


class StoreSummary(BaseModel):
    id: UUID
    name: str
    platform: str
    domain: str
    currency: str | None = None
    timezone: str | None = None
    connection_status: str
    last_successful_sync_at: str | None = None
    created_at: datetime
    updated_at: datetime


class SyncRunSummary(BaseModel):
    id: UUID
    status: str
    mode: str
    records_imported: int
    records_failed: int
    entity_counts_json: dict
    error_summary: str | None = None
    trace_id: str | None = None
    failure_class: str | None = None
    failure_code: str | None = None
    last_error_at: str | None = None
    next_retry_at: str | None = None
    max_retries: int = 0
    attempt_count: int = 0
    started_at: str | None = None
    completed_at: str | None = None
    retry_of_sync_run_id: UUID | None = None
    created_at: datetime


class ProductVariantSummary(BaseModel):
    id: UUID
    external_variant_id: str
    sku: str | None = None
    title: str
    price: str
    compare_at_price: str | None = None
    inventory_quantity: int


class ProductDraftSummary(BaseModel):
    id: UUID
    product_id: UUID
    generated_title: str | None = None
    generated_description: str | None = None
    generated_tags: list[str]
    generated_seo_title: str | None = None
    generated_seo_description: str | None = None
    model_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class ProductSummary(BaseModel):
    id: UUID
    title: str
    handle: str
    vendor: str | None = None
    status: str
    seo_title: str | None = None
    inventory_total: int
    updated_at: str


class ProductDetail(ProductSummary):
    variants: list[ProductVariantSummary] = Field(default_factory=list)
    latest_draft: ProductDraftSummary | None = None


class OrderSummary(BaseModel):
    id: UUID
    external_order_id: str
    status: str
    payment_status: str | None = None
    fulfillment_status: str | None = None
    total: str
    currency: str | None = None
    created_at: str


class CustomerSummary(BaseModel):
    id: UUID
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    total_orders: int
    created_at: str


class ApprovalSummary(BaseModel):
    id: UUID
    status: str
    action_type: str
    entity_type: str
    entity_id: UUID
    reasoning: str
    review_notes: str | None = None
    execution_status: str | None = None
    execution_error: str | None = None
    trace_id: str | None = None
    failure_class: str | None = None
    failure_code: str | None = None
    last_error_at: str | None = None
    next_retry_at: str | None = None
    max_retries: int = 0
    attempt_count: int = 0
    retry_count: int = 0
    expires_at: str
    created_at: str
    updated_at: str


class WorkflowRunSummary(BaseModel):
    id: UUID
    status: str
    trigger_type: str
    workflow_id: UUID | None = None
    created_at: str
    input_payload: dict | None = None
    output_payload: dict | None = None
    error_message: str | None = None
    trace_id: str | None = None
    failure_class: str | None = None
    failure_code: str | None = None
    last_error_at: str | None = None
    next_retry_at: str | None = None
    max_retries: int = 0
    attempt_count: int = 0
    retry_count: int = 0


class AgentRunSummary(BaseModel):
    id: UUID
    status: str
    agent_type: str
    model_name: str
    created_at: str
    workflow_run_id: UUID | None = None
    input_summary: str | None = None
    retrieved_context_summary: str | None = None
    output_summary: str | None = None
    error_message: str | None = None
    trace_id: str | None = None
    failure_class: str | None = None
    failure_code: str | None = None
    last_error_at: str | None = None
    next_retry_at: str | None = None
    max_retries: int = 0
    attempt_count: int = 0


class AuditEventSummary(BaseModel):
    id: UUID
    entity_type: str
    action_type: str
    source_type: str
    outcome: str
    created_at: str
    user_id: UUID | None = None
    metadata_json: dict | None = None


class NotificationSummary(BaseModel):
    id: UUID
    type: str
    channel: str
    title: str
    body: str
    status: str
    read_at: str | None = None
    created_at: str
    store_id: UUID | None = None
