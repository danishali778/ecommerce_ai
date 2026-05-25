from app.modules.notifications import NotificationModule


class NotificationService:
    def __init__(self, db, module: NotificationModule | None = None) -> None:
        self.db = db
        self.module = module or NotificationModule(db)

    def list_notifications(self, user_context: dict, **filters) -> list[dict]:
        return self.module.list_notifications(user_context, **filters)

    def mark_as_read(self, user_context: dict, notification_id) -> dict:
        return self.module.mark_as_read(user_context, notification_id)
