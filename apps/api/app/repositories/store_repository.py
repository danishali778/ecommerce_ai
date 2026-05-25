from uuid import UUID

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import Integration, Store


class StoreRepository(Repository):
    def create_store(self, **values) -> Store:
        store = Store(**values)
        self.db.add(store)
        self.db.flush()
        return store

    def list_stores(self, organization_id: UUID) -> list[Store]:
        return list(self.db.scalars(select(Store).where(Store.organization_id == organization_id).order_by(Store.created_at.desc())))

    def get_store(self, organization_id: UUID, store_id: UUID) -> Store | None:
        return self.db.scalar(select(Store).where(Store.organization_id == organization_id, Store.id == store_id))

    def create_integration(self, **values) -> Integration:
        integration = Integration(**values)
        self.db.add(integration)
        self.db.flush()
        return integration

    def get_integration(self, store_id: UUID, provider: str = "shopify") -> Integration | None:
        return self.db.scalar(select(Integration).where(Integration.store_id == store_id, Integration.provider == provider))

    def update_store(self, store: Store, **values) -> Store:
        for key, value in values.items():
            setattr(store, key, value)
        self.db.flush()
        return store

    def update_integration(self, integration: Integration, **values) -> Integration:
        for key, value in values.items():
            setattr(integration, key, value)
        self.db.flush()
        return integration
