from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class SupportConversationCreateRequest(BaseModel):
    customer_id: UUID | None = None
    order_id: UUID | None = None
    external_ticket_id: str | None = Field(default=None, max_length=255)
    channel: str = Field(default="internal_console", min_length=1, max_length=50)
    assigned_user_id: UUID | None = None


class SupportConversationStatusUpdateRequest(BaseModel):
    status: str = Field(min_length=1, max_length=50)


class SupportMessageCreateRequest(BaseModel):
    direction: str = Field(min_length=1, max_length=50)
    body: str = Field(min_length=1)


class SupportReplyDraftGenerateRequest(BaseModel):
    force_policy_type: str | None = Field(default=None, max_length=50)


class SupportDraftGenerationAcceptedResponse(BaseModel):
    workflow_run_id: UUID
    agent_run_id: UUID
    status: str


class SupportConversationResponse(BaseModel):
    id: UUID
    store_id: UUID
    customer_id: UUID | None = None
    order_id: UUID | None = None
    external_ticket_id: str | None = None
    channel: str
    status: str
    assigned_user_id: UUID | None = None
    created_at: str
    updated_at: str


class SupportMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    direction: str
    body: str
    generated_by_ai: bool
    confidence_score: float | None = None
    needs_human_review: bool
    review_reason_code: str | None = None
    status: str
    cited_policy_chunks_json: list[dict] = Field(default_factory=list)
    cited_order_facts_summary: str | None = None
    created_by_user_id: UUID | None = None
    created_at: str
    updated_at: str
