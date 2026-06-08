from app.modules.notifications import NotificationModule
from app.core.runtime import call_with_optional_trace


class NotificationService:
    def __init__(self, db, module: NotificationModule | None = None) -> None:
        self.db = db
        self.module = module or NotificationModule(db)

    def list_notifications(self, user_context: dict, **filters) -> list[dict]:
        return self.module.list_notifications(user_context, **filters)

    def mark_as_read(self, user_context: dict, notification_id) -> dict:
        return self.module.mark_as_read(user_context, notification_id)

    def list_channels(self, user_context: dict, store_id) -> list[dict]:
        return self.module.list_channels(user_context, store_id)

    def create_channel(self, user_context: dict, store_id, payload) -> dict:
        return self.module.create_channel(user_context, store_id, payload)

    def get_channel(self, user_context: dict, store_id, channel_id) -> dict:
        return self.module.get_channel(user_context, store_id, channel_id)

    def update_channel(self, user_context: dict, store_id, channel_id, payload) -> dict:
        return self.module.update_channel(user_context, store_id, channel_id, payload)

    def delete_channel(self, user_context: dict, store_id, channel_id) -> dict:
        return self.module.delete_channel(user_context, store_id, channel_id)

    def test_channel(self, user_context: dict, store_id, channel_id, trace_id: str | None = None) -> dict:
        return call_with_optional_trace(self.module.test_channel, user_context, store_id, channel_id, trace_id=trace_id)

    def list_deliveries(self, user_context: dict, store_id, status: str | None = None) -> list[dict]:
        return self.module.list_deliveries(user_context, store_id, status=status)

    def get_delivery(self, user_context: dict, store_id, delivery_id) -> dict:
        return self.module.get_delivery(user_context, store_id, delivery_id)

    def retry_delivery(self, user_context: dict, store_id, delivery_id, trace_id: str | None = None) -> dict:
        result = call_with_optional_trace(self.module.retry_delivery, user_context, store_id, delivery_id, trace_id=trace_id)
        if result.pop("_enqueue_delivery", False):
            call_with_optional_trace(self._enqueue_delivery, result["id"], trace_id=trace_id)
        return result

    def list_preferences(self, user_context: dict, store_id) -> list[dict]:
        return self.module.list_preferences(user_context, store_id)

    def update_preference(self, user_context: dict, store_id, preference_id, payload) -> dict:
        return self.module.update_preference(user_context, store_id, preference_id, payload)

    @staticmethod
    def _enqueue_delivery(delivery_id: str, trace_id: str | None = None) -> None:
        from app.tasks.notifications import send_external_notification_delivery

        send_external_notification_delivery.delay(delivery_id, trace_id)
