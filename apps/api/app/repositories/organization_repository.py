from uuid import UUID

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import Organization


class OrganizationRepository(Repository):
    def get_by_id(self, organization_id: UUID) -> Organization | None:
        return self.db.scalar(select(Organization).where(Organization.id == organization_id))

    def get_by_slug(self, slug: str) -> Organization | None:
        return self.db.scalar(select(Organization).where(Organization.slug == slug))

    def create(self, **values) -> Organization:
        organization = Organization(**values)
        self.db.add(organization)
        self.db.flush()
        return organization
