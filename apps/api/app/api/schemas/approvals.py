from pydantic import BaseModel

from app.api.schemas.common import ApprovalSummary


class ApprovalDecisionRequest(BaseModel):
    review_notes: str | None = None


class ApprovalResponse(ApprovalSummary):
    workflow_run_id: str | None = None
    agent_run_id: str | None = None
    proposed_action_json: dict | None = None


class ApprovalActionResponse(ApprovalSummary):
    workflow_run_id: str | None = None
    agent_run_id: str | None = None
    proposed_action_json: dict | None = None
