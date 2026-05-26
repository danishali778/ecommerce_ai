from __future__ import annotations

from pydantic import BaseModel, Field


class SupportAgentCitation(BaseModel):
    chunk_id: str
    rationale: str = ""


class SupportAgentOutput(BaseModel):
    draft_body: str = Field(min_length=1)
    confidence_score: float = Field(ge=0.0, le=1.0)
    needs_human_review: bool
    review_reason_code: str | None = None
    cited_policy_chunks: list[SupportAgentCitation] = Field(default_factory=list)
    cited_order_facts_summary: str = ""
