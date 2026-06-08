from datetime import datetime, timezone
from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.repositories.notification_repository import NotificationRepository
from app.repositories.store_repository import StoreRepository

from .delivery import DEFAULT_EVENT_TYPES, mask_channel_metadata, queue_channel_test_delivery
from .serializers import serialize_notification


class NotificationModule:
    def __init__(self, db) -> None:
        self.db = db
        self.repository = NotificationRepository(db)
        self.store_repository = StoreRepository(db)

    def list_notifications(
        self,
        user_context: dict,
        *,
        status: str | None = None,
        notification_type: str | None = None,
        store_id: UUID | None = None,
    ) -> list[dict]:
        require_permission(user_context, Permission.NOTIFICATIONS_READ)
        organization = self._require_org(user_context)
        notifications = self.repository.list_for_user(
            UUID(organization["id"]),
            UUID(user_context["user"]["id"]),
            status=status,
            notification_type=notification_type,
            store_id=store_id,
        )
        return [serialize_notification(notification) for notification in notifications]

    def mark_as_read(self, user_context: dict, notification_id: UUID) -> dict:
        require_permission(user_context, Permission.NOTIFICATIONS_UPDATE)
        organization = self._require_org(user_context)
        notification = self.repository.get_for_user(UUID(organization["id"]), UUID(user_context["user"]["id"]), notification_id)
        if notification is None:
            raise AppError(code="not_found", message="Notification not found", status_code=404)
        if notification.status != "read":
            notification = self.repository.update(notification, status="read", read_at=datetime.now(timezone.utc))
        self.db.commit()
        return serialize_notification(notification)

    def list_channels(self, user_context: dict, store_id: UUID) -> list[dict]:
        organization_id = self._require_store_scope(user_context, store_id)
        require_permission(user_context, Permission.NOTIFICATIONS_MANAGE)
        channels = self.repository.list_channels(organization_id, store_id)
        return [self._serialize_channel(channel) for channel in channels]

    def create_channel(self, user_context: dict, store_id: UUID, payload) -> dict:
        organization_id = self._require_store_scope(user_context, store_id)
        require_permission(user_context, Permission.NOTIFICATIONS_MANAGE)
        secret_reference = None
        if payload.secret_value:
            from app.core.secret_store import get_secret_store

            secret_reference = get_secret_store().put(payload.secret_value)
        channel = self.repository.create_channel(
            organization_id=organization_id,
            store_id=store_id,
            name=payload.name,
            channel_type=payload.channel_type,
            status="connected",
            is_enabled=payload.is_enabled,
            metadata_json=payload.metadata_json,
            secret_reference=secret_reference,
            last_test_status=None,
            last_test_error=None,
            last_tested_at=None,
            created_by_user_id=UUID(user_context["user"]["id"]),
            updated_by_user_id=UUID(user_context["user"]["id"]),
        )
        for event_type in DEFAULT_EVENT_TYPES:
            self.repository.create_preference(
                organization_id=organization_id,
                store_id=store_id,
                channel_id=channel.id,
                event_type=event_type,
                is_enabled=False,
            )
        self.db.commit()
        return self._serialize_channel(channel)

    def get_channel(self, user_context: dict, store_id: UUID, channel_id: UUID) -> dict:
        organization_id = self._require_store_scope(user_context, store_id)
        require_permission(user_context, Permission.NOTIFICATIONS_MANAGE)
        channel = self.repository.get_channel(organization_id, store_id, channel_id)
        if channel is None:
            raise AppError(code="not_found", message="Notification channel not found", status_code=404)
        return self._serialize_channel(channel)

    def update_channel(self, user_context: dict, store_id: UUID, channel_id: UUID, payload) -> dict:
        organization_id = self._require_store_scope(user_context, store_id)
        require_permission(user_context, Permission.NOTIFICATIONS_MANAGE)
        channel = self.repository.get_channel(organization_id, store_id, channel_id)
        if channel is None:
            raise AppError(code="not_found", message="Notification channel not found", status_code=404)
        updates = {"updated_by_user_id": UUID(user_context["user"]["id"])}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.is_enabled is not None:
            updates["is_enabled"] = payload.is_enabled
        if payload.metadata_json is not None:
            updates["metadata_json"] = payload.metadata_json
        if payload.secret_value is not None:
            from app.core.secret_store import get_secret_store

            store = get_secret_store()
            updates["secret_reference"] = store.rotate(channel.secret_reference, payload.secret_value) if channel.secret_reference else store.put(payload.secret_value)
        channel = self.repository.update_channel(channel, **updates)
        self.db.commit()
        return self._serialize_channel(channel)

    def delete_channel(self, user_context: dict, store_id: UUID, channel_id: UUID) -> dict:
        organization_id = self._require_store_scope(user_context, store_id)
        require_permission(user_context, Permission.NOTIFICATIONS_MANAGE)
        channel = self.repository.get_channel(organization_id, store_id, channel_id)
        if channel is None:
            raise AppError(code="not_found", message="Notification channel not found", status_code=404)
        self.repository.delete_channel(channel)
        self.db.commit()
        return {"deleted": True, "channel_id": str(channel.id)}

    def test_channel(self, user_context: dict, store_id: UUID, channel_id: UUID, trace_id: str | None = None) -> dict:
        organization_id = self._require_store_scope(user_context, store_id)
        require_permission(user_context, Permission.NOTIFICATIONS_MANAGE)
        channel = self.repository.get_channel(organization_id, store_id, channel_id)
        if channel is None:
            raise AppError(code="not_found", message="Notification channel not found", status_code=404)
        delivery = queue_channel_test_delivery(self.db, channel, UUID(user_context["user"]["id"]), trace_id=trace_id)
        self.db.commit()
        return {
            "channel_id": str(channel.id),
            "status": "queued",
            "delivery_id": str(delivery.id),
            "message": "Test delivery queued",
        }

    def list_deliveries(self, user_context: dict, store_id: UUID, *, status: str | None = None) -> list[dict]:
        organization_id = self._require_store_scope(user_context, store_id)
        require_permission(user_context, Permission.NOTIFICATIONS_MANAGE)
        deliveries = self.repository.list_deliveries(organization_id, store_id, status=status)
        return [self._serialize_delivery(delivery) for delivery in deliveries]

    def get_delivery(self, user_context: dict, store_id: UUID, delivery_id: UUID) -> dict:
        organization_id = self._require_store_scope(user_context, store_id)
        require_permission(user_context, Permission.NOTIFICATIONS_MANAGE)
        delivery = self.repository.get_delivery_in_scope(organization_id, store_id, delivery_id)
        if delivery is None:
            raise AppError(code="not_found", message="Notification delivery not found", status_code=404)
        return self._serialize_delivery(delivery)

    def retry_delivery(self, user_context: dict, store_id: UUID, delivery_id: UUID, trace_id: str | None = None) -> dict:
        organization_id = self._require_store_scope(user_context, store_id)
        require_permission(user_context, Permission.NOTIFICATIONS_MANAGE)
        delivery = self.repository.get_delivery_in_scope(organization_id, store_id, delivery_id)
        if delivery is None:
            raise AppError(code="not_found", message="Notification delivery not found", status_code=404)
        if delivery.status not in {"failed", "queued"}:
            raise AppError(code="conflict", message="Notification delivery is not retryable", status_code=409)
        delivery = self.repository.update_delivery(
            delivery,
            status="queued",
            trace_id=trace_id or delivery.trace_id,
            last_error=None,
            failure_class=None,
            failure_code=None,
            next_retry_at=None,
            terminal_failed_at=None,
        )
        self.db.commit()
        response = self._serialize_delivery(delivery)
        response["_enqueue_delivery"] = True
        return response

    def list_preferences(self, user_context: dict, store_id: UUID) -> list[dict]:
        organization_id = self._require_store_scope(user_context, store_id)
        require_permission(user_context, Permission.NOTIFICATIONS_MANAGE)
        preferences = self.repository.list_preferences(organization_id, store_id)
        return [self._serialize_preference(preference) for preference in preferences]

    def update_preference(self, user_context: dict, store_id: UUID, preference_id: UUID, payload) -> dict:
        organization_id = self._require_store_scope(user_context, store_id)
        require_permission(user_context, Permission.NOTIFICATIONS_MANAGE)
        preference = self.repository.get_preference(organization_id, store_id, preference_id)
        if preference is None:
            raise AppError(code="not_found", message="Notification preference not found", status_code=404)
        preference = self.repository.update_preference(preference, is_enabled=payload.is_enabled)
        self.db.commit()
        return self._serialize_preference(preference)

    @staticmethod
    def _require_org(user_context: dict) -> dict:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        return organization

    def _require_store_scope(self, user_context: dict, store_id: UUID) -> UUID:
        organization = self._require_org(user_context)
        organization_id = UUID(organization["id"])
        store = self.store_repository.get_store(organization_id, store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return organization_id

    @staticmethod
    def _serialize_channel(channel) -> dict:
        return {
            "id": str(channel.id),
            "store_id": str(channel.store_id),
            "name": channel.name,
            "channel_type": channel.channel_type,
            "status": channel.status,
            "is_enabled": channel.is_enabled,
            "metadata_json": mask_channel_metadata(channel.channel_type, channel.metadata_json),
            "has_secret": bool(channel.secret_reference),
            "last_test_status": channel.last_test_status,
            "last_test_error": channel.last_test_error,
            "last_tested_at": channel.last_tested_at.isoformat() if channel.last_tested_at else None,
            "created_at": channel.created_at,
            "updated_at": channel.updated_at,
        }

    @staticmethod
    def _serialize_preference(preference) -> dict:
        return {
            "id": str(preference.id),
            "channel_id": str(preference.channel_id),
            "event_type": preference.event_type,
            "is_enabled": preference.is_enabled,
            "created_at": preference.created_at,
            "updated_at": preference.updated_at,
        }

    @staticmethod
    def _serialize_delivery(delivery) -> dict:
        return {
            "id": str(delivery.id),
            "notification_id": str(delivery.notification_id),
            "channel_id": str(delivery.channel_id),
            "event_type": delivery.event_type,
            "status": delivery.status,
            "trace_id": delivery.trace_id,
            "failure_class": delivery.failure_class,
            "failure_code": delivery.failure_code,
            "last_error": delivery.last_error,
            "last_error_at": delivery.last_error_at.isoformat() if delivery.last_error_at else None,
            "next_retry_at": delivery.next_retry_at.isoformat() if delivery.next_retry_at else None,
            "max_retries": delivery.max_retries,
            "attempt_count": delivery.attempt_count,
            "queued_at": delivery.queued_at.isoformat(),
            "last_attempted_at": delivery.last_attempted_at.isoformat() if delivery.last_attempted_at else None,
            "sent_at": delivery.sent_at.isoformat() if delivery.sent_at else None,
            "created_at": delivery.created_at.isoformat(),
            "rendered_payload_json": delivery.rendered_payload_json,
            "response_payload_json": delivery.response_payload_json,
        }
