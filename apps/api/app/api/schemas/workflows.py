from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


WorkflowTrigger = Literal[
    "sync.completed",
    "order.imported",
    "inventory.below_threshold",
    "pricing.recommendation.created",
    "approval.pending",
    "workflow.failed",
]

WorkflowOperator = Literal["gt", "gte", "lt", "lte", "eq", "neq", "in", "bool_is"]
WorkflowActionType = Literal[
    "create_alert",
    "create_approval",
    "enqueue_agent",
    "send_external_notification",
    "create_inventory_alert",
    "create_pricing_recommendation",
    "log_audit_event",
]


class WorkflowCondition(BaseModel):
    field: str = Field(min_length=1, max_length=100)
    operator: WorkflowOperator
    value: Any


class WorkflowConditionGroup(BaseModel):
    match: Literal["all", "any"] = "all"
    conditions: list[WorkflowCondition] = Field(default_factory=list)


class WorkflowAction(BaseModel):
    type: WorkflowActionType
    params: dict[str, Any] = Field(default_factory=dict)


class WorkflowCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    enabled: bool = True
    phase_scope: Literal["p2"] = "p2"
    trigger: WorkflowTrigger
    condition_groups: list[WorkflowConditionGroup] = Field(default_factory=list)
    actions: list[WorkflowAction] = Field(default_factory=list)
    approval_required: bool = False


class WorkflowUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    enabled: bool | None = None
    trigger: WorkflowTrigger | None = None
    condition_groups: list[WorkflowConditionGroup] | None = None
    actions: list[WorkflowAction] | None = None
    approval_required: bool | None = None


class WorkflowResponse(BaseModel):
    id: UUID
    store_id: UUID | None = None
    name: str
    key: str
    description: str | None = None
    phase_scope: str
    trigger: str
    condition_groups: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    approval_required: bool
    enabled: bool
    is_system_defined: bool
    version_number: int
    created_at: datetime
    updated_at: datetime


class WorkflowTestRequest(BaseModel):
    event_payload: dict[str, Any] = Field(default_factory=dict)
    event_entity_type: str = "manual_test"
    event_entity_id: UUID | None = None


class WorkflowTestResponse(BaseModel):
    status: str
    matched: bool
    workflow_run_id: UUID | None = None
    results: dict[str, Any]

