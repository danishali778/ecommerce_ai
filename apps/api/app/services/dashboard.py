from app.modules.dashboard import DashboardModule


class DashboardService:
    def __init__(self, db, module: DashboardModule | None = None) -> None:
        self.db = db
        self.module = module or DashboardModule(db)

    def get_summary(self, user_context: dict, store_id) -> dict:
        return self.module.get_summary(user_context, store_id)

    def list_workflow_runs(self, user_context: dict, store_id, **filters) -> list[dict]:
        return self.module.list_workflow_runs(user_context, store_id, **filters)

    def get_workflow_run(self, user_context: dict, store_id, workflow_run_id) -> dict:
        return self.module.get_workflow_run(user_context, store_id, workflow_run_id)

    def list_agent_runs(self, user_context: dict, store_id, **filters) -> list[dict]:
        return self.module.list_agent_runs(user_context, store_id, **filters)

    def get_agent_run(self, user_context: dict, store_id, agent_run_id) -> dict:
        return self.module.get_agent_run(user_context, store_id, agent_run_id)

    def list_audit_events(self, user_context: dict, store_id, **filters) -> list[dict]:
        return self.module.list_audit_events(user_context, store_id, **filters)
