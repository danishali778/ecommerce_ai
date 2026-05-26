from app.modules.analytics import AnalyticsModule


class AnalyticsService:
    def __init__(self, db, module: AnalyticsModule | None = None) -> None:
        self.db = db
        self.module = module or AnalyticsModule(db)

    def get_overview(self, user_context: dict, store_id, date_from=None, date_to=None) -> dict:
        return self.module.get_overview(user_context, store_id, date_from=date_from, date_to=date_to)

    def get_automation(self, user_context: dict, store_id, date_from=None, date_to=None) -> dict:
        return self.module.get_automation(user_context, store_id, date_from=date_from, date_to=date_to)
