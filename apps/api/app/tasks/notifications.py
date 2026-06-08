from uuid import UUID

from app.core.celery_app import celery_app
from app.core.settings import get_settings
from app.modules.notifications.delivery import deliver_notification_delivery
from app.repositories.models import NotificationDelivery
from app.tasks.runtime import execute_tracked_task


@celery_app.task(name="app.tasks.notifications.send_external_notification_delivery", bind=True)
def send_external_notification_delivery(self, delivery_id: str, trace_id: str | None = None) -> None:
    settings = get_settings()

    def subject_loader(db):
        return db.get(NotificationDelivery, UUID(delivery_id))

    def operation(db, active_trace_id: str):
        deliver_notification_delivery(db, delivery_id, trace_id=active_trace_id)

    execute_tracked_task(
        task=self,
        subject_type="notification_delivery",
        subject_id=UUID(delivery_id),
        organization_id=None,
        store_id=None,
        subject_loader=subject_loader,
        operation=operation,
        max_retries=settings.notification_retry_max_retries,
        base_delay_seconds=settings.notification_retry_base_delay_seconds,
        trace_id=trace_id,
    )
