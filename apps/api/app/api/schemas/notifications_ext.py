from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationChannelCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    channel_type: str = Field(pattern="^(webhook|email)$")
    is_enabled: bool = True
    metadata_json: dict = Field(default_factory=dict)
    secret_value: str | None = None


class NotificationChannelUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_enabled: bool | None = None
    metadata_json: dict | None = None
    secret_value: str | None = None


class NotificationChannelResponse(BaseModel):
    id: UUID
    store_id: UUID
    name: str
    channel_type: str
    status: str
    is_enabled: bool
    metadata_json: dict
    has_secret: bool
    last_test_status: str | None = None
    last_test_error: str | None = None
    last_tested_at: str | None = None
    created_at: datetime
    updated_at: datetime


class NotificationPreferenceResponse(BaseModel):
    id: UUID
    channel_id: UUID
    event_type: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class NotificationPreferenceUpdateRequest(BaseModel):
    is_enabled: bool


class NotificationChannelTestResponse(BaseModel):
    channel_id: UUID
    status: str
    delivery_id: UUID | None = None
    message: str


class NotificationDeliveryResponse(BaseModel):
    id: UUID
    notification_id: UUID
    channel_id: UUID
    event_type: str
    status: str
    trace_id: str | None = None
    failure_class: str | None = None
    failure_code: str | None = None
    last_error: str | None = None
    last_error_at: str | None = None
    next_retry_at: str | None = None
    max_retries: int
    attempt_count: int
    queued_at: str
    last_attempted_at: str | None = None
    sent_at: str | None = None
    created_at: str
    rendered_payload_json: dict
    response_payload_json: dict
