from uuid import UUID

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import Notification


class NotificationRepository(Repository):
    def list_for_user(
        self,
        organization_id: UUID,
        user_id: UUID,
        *,
        status: str | None = None,
        notification_type: str | None = None,
        store_id: UUID | None = None,
    ) -> list[Notification]:
        query = (
            select(Notification)
            .where(Notification.organization_id == organization_id, Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        if status:
            query = query.where(Notification.status == status)
        if notification_type:
            query = query.where(Notification.type == notification_type)
        if store_id:
            query = query.where(Notification.store_id == store_id)
        return list(self.db.scalars(query))

    def get_for_user(self, organization_id: UUID, user_id: UUID, notification_id: UUID) -> Notification | None:
        return self.db.scalar(
            select(Notification).where(
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
                Notification.id == notification_id,
            )
        )

    def update(self, notification: Notification, **values) -> Notification:
        for key, value in values.items():
            setattr(notification, key, value)
        self.db.flush()
        return notification
