from app.modules.inventory import InventoryModule


class InventoryService:
    def __init__(self, db, module: InventoryModule | None = None) -> None:
        self.db = db
        self.module = module or InventoryModule(db)

    def list_alerts(self, user_context: dict, store_id, status: str | None = None) -> list[dict]:
        return self.module.list_alerts(user_context, store_id, status=status)

    def list_reorder_suggestions(self, user_context: dict, store_id, status: str | None = None) -> list[dict]:
        return self.module.list_reorder_suggestions(user_context, store_id, status=status)

    def get_reorder_suggestion(self, user_context: dict, store_id, suggestion_id) -> dict:
        return self.module.get_reorder_suggestion(user_context, store_id, suggestion_id)

    def create_or_refresh_supplier_draft(self, user_context: dict, store_id, suggestion_id, payload) -> dict:
        return self.module.create_or_refresh_supplier_draft(user_context, store_id, suggestion_id, payload)
