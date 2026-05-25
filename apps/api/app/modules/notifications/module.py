from datetime import datetime, timezone
from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.repositories.notification_repository import NotificationRepository

from .serializers import serialize_notification


class NotificationModule:
    def __init__(self, db) -> None:
        self.db = db
        self.repository = NotificationRepository(db)

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

    @staticmethod
    def _require_org(user_context: dict) -> dict:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        return organization
