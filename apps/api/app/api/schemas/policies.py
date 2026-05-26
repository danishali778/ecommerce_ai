from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class PolicyDocumentCreateRequest(BaseModel):
    document_type: str = Field(min_length=1, max_length=50)
    source_type: str = Field(default="manual", min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    version: str | None = Field(default=None, max_length=100)


class PolicyDocumentUpdateRequest(BaseModel):
    document_type: str | None = Field(default=None, min_length=1, max_length=50)
    source_type: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    version: str | None = Field(default=None, max_length=100)


class PolicyDocumentResponse(BaseModel):
    id: UUID
    store_id: UUID
    document_type: str
    source_type: str
    title: str
    content: str
    version: str | None = None
    is_active: bool
    embedding_status: str
    created_at: str
    updated_at: str
