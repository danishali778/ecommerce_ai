from uuid import UUID

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import ApprovalRequest, ProductContentDraft


class CatalogRepository(Repository):
    def create_draft(self, **values) -> ProductContentDraft:
        draft = ProductContentDraft(**values)
        self.db.add(draft)
        self.db.flush()
        return draft

    def list_drafts(self, organization_id: UUID, store_id: UUID, product_id: UUID) -> list[ProductContentDraft]:
        return list(
            self.db.scalars(
                select(ProductContentDraft)
                .where(
                    ProductContentDraft.organization_id == organization_id,
                    ProductContentDraft.store_id == store_id,
                    ProductContentDraft.product_id == product_id,
                )
                .order_by(ProductContentDraft.created_at.desc())
            )
        )

    def get_draft(self, organization_id: UUID, store_id: UUID, product_id: UUID, draft_id: UUID) -> ProductContentDraft | None:
        return self.db.scalar(
            select(ProductContentDraft).where(
                ProductContentDraft.organization_id == organization_id,
                ProductContentDraft.store_id == store_id,
                ProductContentDraft.product_id == product_id,
                ProductContentDraft.id == draft_id,
            )
        )

    def update_draft(self, draft: ProductContentDraft, **values) -> ProductContentDraft:
        for key, value in values.items():
            setattr(draft, key, value)
        self.db.flush()
        return draft

    def create_approval_request(self, **values) -> ApprovalRequest:
        approval_request = ApprovalRequest(**values)
        self.db.add(approval_request)
        self.db.flush()
        return approval_request
