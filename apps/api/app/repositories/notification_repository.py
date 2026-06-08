from uuid import UUID

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import Notification, NotificationChannel, NotificationDelivery, NotificationPreference


class NotificationRepository(Repository):
    def create_notification(self, **values) -> Notification:
        notification = Notification(
            **values,
        )
        self.db.add(notification)
        self.db.flush()
        return notification

    def create_for_test_notification(self, **values) -> Notification:
        return self.create_notification(
            type="notification_channel_test",
            channel="in_app",
            status="unread",
            **values,
        )

    def get_notification(self, notification_id: UUID) -> Notification | None:
        return self.db.get(Notification, notification_id)

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

    def list_channels(self, organization_id: UUID, store_id: UUID) -> list[NotificationChannel]:
        query = (
            select(NotificationChannel)
            .where(NotificationChannel.organization_id == organization_id, NotificationChannel.store_id == store_id)
            .order_by(NotificationChannel.updated_at.desc())
        )
        return list(self.db.scalars(query))

    def get_channel(self, organization_id: UUID, store_id: UUID, channel_id: UUID) -> NotificationChannel | None:
        return self.db.scalar(
            select(NotificationChannel).where(
                NotificationChannel.organization_id == organization_id,
                NotificationChannel.store_id == store_id,
                NotificationChannel.id == channel_id,
            )
        )

    def create_channel(self, **values) -> NotificationChannel:
        channel = NotificationChannel(**values)
        self.db.add(channel)
        self.db.flush()
        return channel

    def update_channel(self, channel: NotificationChannel, **values) -> NotificationChannel:
        for key, value in values.items():
            setattr(channel, key, value)
        self.db.flush()
        return channel

    def delete_channel(self, channel: NotificationChannel) -> None:
        self.db.delete(channel)
        self.db.flush()

    def list_preferences(self, organization_id: UUID, store_id: UUID) -> list[NotificationPreference]:
        query = (
            select(NotificationPreference)
            .where(NotificationPreference.organization_id == organization_id, NotificationPreference.store_id == store_id)
            .order_by(NotificationPreference.updated_at.desc())
        )
        return list(self.db.scalars(query))

    def get_preference(self, organization_id: UUID, store_id: UUID, preference_id: UUID) -> NotificationPreference | None:
        return self.db.scalar(
            select(NotificationPreference).where(
                NotificationPreference.organization_id == organization_id,
                NotificationPreference.store_id == store_id,
                NotificationPreference.id == preference_id,
            )
        )

    def create_preference(self, **values) -> NotificationPreference:
        preference = NotificationPreference(**values)
        self.db.add(preference)
        self.db.flush()
        return preference

    def update_preference(self, preference: NotificationPreference, **values) -> NotificationPreference:
        for key, value in values.items():
            setattr(preference, key, value)
        self.db.flush()
        return preference

    def list_enabled_channels_for_event(self, organization_id: UUID, store_id: UUID, event_type: str) -> list[NotificationChannel]:
        query = (
            select(NotificationChannel)
            .join(NotificationPreference, NotificationPreference.channel_id == NotificationChannel.id)
            .where(
                NotificationChannel.organization_id == organization_id,
                NotificationChannel.store_id == store_id,
                NotificationChannel.is_enabled.is_(True),
                NotificationPreference.event_type == event_type,
                NotificationPreference.is_enabled.is_(True),
            )
            .order_by(NotificationChannel.updated_at.desc())
        )
        return list(self.db.scalars(query))

    def create_delivery(self, **values) -> NotificationDelivery:
        delivery = NotificationDelivery(**values)
        self.db.add(delivery)
        self.db.flush()
        return delivery

    def get_delivery(self, delivery_id: UUID) -> NotificationDelivery | None:
        return self.db.get(NotificationDelivery, delivery_id)

    def get_delivery_in_scope(self, organization_id: UUID, store_id: UUID, delivery_id: UUID) -> NotificationDelivery | None:
        return self.db.scalar(
            select(NotificationDelivery).where(
                NotificationDelivery.organization_id == organization_id,
                NotificationDelivery.store_id == store_id,
                NotificationDelivery.id == delivery_id,
            )
        )

    def update_delivery(self, delivery: NotificationDelivery, **values) -> NotificationDelivery:
        for key, value in values.items():
            setattr(delivery, key, value)
        self.db.flush()
        return delivery

    def list_deliveries(self, organization_id: UUID, store_id: UUID, *, status: str | None = None) -> list[NotificationDelivery]:
        query = (
            select(NotificationDelivery)
            .where(NotificationDelivery.organization_id == organization_id, NotificationDelivery.store_id == store_id)
            .order_by(NotificationDelivery.created_at.desc())
        )
        if status:
            query = query.where(NotificationDelivery.status == status)
        return list(self.db.scalars(query))
