from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import RiskReview


class FraudRepository(Repository):
    def get_pending_review_for_order(self, order_id: UUID) -> RiskReview | None:
        return self.db.scalar(
            select(RiskReview).where(
                RiskReview.order_id == order_id,
                RiskReview.risk_status == "pending_review",
            )
        )

    def create_review(self, **values) -> RiskReview:
        review = RiskReview(**values)
        self.db.add(review)
        self.db.flush()
        return review

    def update_review(self, review: RiskReview, **values) -> RiskReview:
        for key, value in values.items():
            setattr(review, key, value)
        self.db.flush()
        return review

    def list_reviews(self, organization_id: UUID, store_id: UUID, *, risk_status: str | None = None) -> list[RiskReview]:
        query = (
            select(RiskReview)
            .where(RiskReview.organization_id == organization_id, RiskReview.store_id == store_id)
            .order_by(RiskReview.created_at.desc())
        )
        if risk_status:
            query = query.where(RiskReview.risk_status == risk_status)
        return list(self.db.scalars(query))

    def get_review(self, organization_id: UUID, store_id: UUID, review_id: UUID) -> RiskReview | None:
        return self.db.scalar(
            select(RiskReview).where(
                RiskReview.organization_id == organization_id,
                RiskReview.store_id == store_id,
                RiskReview.id == review_id,
            )
        )
