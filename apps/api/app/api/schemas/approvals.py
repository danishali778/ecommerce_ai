from pydantic import BaseModel

from app.api.schemas.common import ApprovalSummary


class ApprovalDecisionRequest(BaseModel):
    review_notes: str | None = None


class ApprovalResponse(ApprovalSummary):
    pass


class ApprovalActionResponse(ApprovalSummary):
    pass
