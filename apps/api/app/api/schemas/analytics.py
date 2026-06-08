from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyticsRangeResponse(BaseModel):
    date_from: str
    date_to: str


class AnalyticsErrorResponse(BaseModel):
    section: str
    message: str


class AnalyticsOverviewSections(BaseModel):
    sales: dict = Field(default_factory=dict)
    inventory: dict = Field(default_factory=dict)
    support: dict = Field(default_factory=dict)
    fraud: dict = Field(default_factory=dict)
    operations: dict = Field(default_factory=dict)
    pricing: dict = Field(default_factory=dict)
    workflows: dict = Field(default_factory=dict)
    notifications: dict = Field(default_factory=dict)


class AnalyticsOverviewResponse(BaseModel):
    range: AnalyticsRangeResponse
    generated_at: str
    sections: AnalyticsOverviewSections
    partial_errors: list[AnalyticsErrorResponse] | None = None


class AnalyticsAutomationResponse(BaseModel):
    range: AnalyticsRangeResponse
    generated_at: str
    sections: dict = Field(default_factory=dict)
    partial_errors: list[AnalyticsErrorResponse] | None = None
