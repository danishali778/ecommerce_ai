from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import InventoryAlert, ReorderSuggestion, SupplierReorderDraft


class InventoryRepository(Repository):
    def get_open_alert_for_variant(self, organization_id: UUID, store_id: UUID, variant_id: UUID) -> InventoryAlert | None:
        return self.db.scalar(
            select(InventoryAlert).where(
                InventoryAlert.organization_id == organization_id,
                InventoryAlert.store_id == store_id,
                InventoryAlert.variant_id == variant_id,
                InventoryAlert.status == "open",
            )
        )

    def create_alert(self, **values) -> InventoryAlert:
        alert = InventoryAlert(**values)
        self.db.add(alert)
        self.db.flush()
        return alert

    def update_alert(self, alert: InventoryAlert, **values) -> InventoryAlert:
        for key, value in values.items():
            setattr(alert, key, value)
        self.db.flush()
        return alert

    def list_alerts(self, organization_id: UUID, store_id: UUID, *, status: str | None = None) -> list[InventoryAlert]:
        query = (
            select(InventoryAlert)
            .where(InventoryAlert.organization_id == organization_id, InventoryAlert.store_id == store_id)
            .order_by(InventoryAlert.created_at.desc())
        )
        if status:
            query = query.where(InventoryAlert.status == status)
        return list(self.db.scalars(query))

    def get_alert(self, organization_id: UUID, store_id: UUID, alert_id: UUID) -> InventoryAlert | None:
        return self.db.scalar(
            select(InventoryAlert).where(
                InventoryAlert.organization_id == organization_id,
                InventoryAlert.store_id == store_id,
                InventoryAlert.id == alert_id,
            )
        )

    def get_active_suggestion_for_alert(self, alert_id: UUID) -> ReorderSuggestion | None:
        return self.db.scalar(
            select(ReorderSuggestion).where(
                ReorderSuggestion.inventory_alert_id == alert_id,
                ReorderSuggestion.status.in_(("open", "drafted")),
            )
        )

    def create_suggestion(self, **values) -> ReorderSuggestion:
        suggestion = ReorderSuggestion(**values)
        self.db.add(suggestion)
        self.db.flush()
        return suggestion

    def update_suggestion(self, suggestion: ReorderSuggestion, **values) -> ReorderSuggestion:
        for key, value in values.items():
            setattr(suggestion, key, value)
        self.db.flush()
        return suggestion

    def list_suggestions(self, organization_id: UUID, store_id: UUID, *, status: str | None = None) -> list[ReorderSuggestion]:
        query = (
            select(ReorderSuggestion)
            .where(ReorderSuggestion.organization_id == organization_id, ReorderSuggestion.store_id == store_id)
            .order_by(ReorderSuggestion.created_at.desc())
        )
        if status:
            query = query.where(ReorderSuggestion.status == status)
        return list(self.db.scalars(query))

    def get_suggestion(self, organization_id: UUID, store_id: UUID, suggestion_id: UUID) -> ReorderSuggestion | None:
        return self.db.scalar(
            select(ReorderSuggestion).where(
                ReorderSuggestion.organization_id == organization_id,
                ReorderSuggestion.store_id == store_id,
                ReorderSuggestion.id == suggestion_id,
            )
        )

    def get_draft_for_suggestion(self, suggestion_id: UUID) -> SupplierReorderDraft | None:
        return self.db.scalar(
            select(SupplierReorderDraft).where(SupplierReorderDraft.reorder_suggestion_id == suggestion_id)
        )

    def create_draft(self, **values) -> SupplierReorderDraft:
        draft = SupplierReorderDraft(**values)
        self.db.add(draft)
        self.db.flush()
        return draft

    def update_draft(self, draft: SupplierReorderDraft, **values) -> SupplierReorderDraft:
        for key, value in values.items():
            setattr(draft, key, value)
        self.db.flush()
        return draft

