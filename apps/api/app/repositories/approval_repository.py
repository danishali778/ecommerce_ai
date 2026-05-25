from uuid import UUID

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import ApprovalRequest


class ApprovalRepository(Repository):
    def list_approvals(self, organization_id: UUID) -> list[ApprovalRequest]:
        return list(
            self.db.scalars(
                select(ApprovalRequest)
                .where(ApprovalRequest.organization_id == organization_id)
                .order_by(ApprovalRequest.created_at.desc())
            )
        )

    def get_approval(self, organization_id: UUID, approval_id: UUID) -> ApprovalRequest | None:
        return self.db.scalar(
            select(ApprovalRequest).where(
                ApprovalRequest.organization_id == organization_id,
                ApprovalRequest.id == approval_id,
            )
        )

    def update_approval(self, approval: ApprovalRequest, **values) -> ApprovalRequest:
        for key, value in values.items():
            setattr(approval, key, value)
        self.db.flush()
        return approval
