from app.modules.inventory import InventoryModule
from app.core.runtime import call_with_optional_trace


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

    def execute_generation(self, agent_run_id: str, trace_id: str | None = None) -> None:
        call_with_optional_trace(self.module.agent_runner.execute_generation, agent_run_id, trace_id=trace_id)
