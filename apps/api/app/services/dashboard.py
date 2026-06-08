from app.modules.dashboard import DashboardModule
from app.core.runtime import call_with_optional_trace


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

    def retry_workflow_run(self, user_context: dict, store_id, workflow_run_id, trace_id: str | None = None) -> dict:
        result = call_with_optional_trace(
            self.module.retry_workflow_run,
            user_context,
            store_id,
            workflow_run_id,
            trace_id=trace_id,
        )
        if result.pop("_enqueue_workflow_run", False):
            call_with_optional_trace(self._enqueue_workflow_run, result["id"], trace_id=trace_id)
        return result

    def list_agent_runs(self, user_context: dict, store_id, **filters) -> list[dict]:
        return self.module.list_agent_runs(user_context, store_id, **filters)

    def get_agent_run(self, user_context: dict, store_id, agent_run_id) -> dict:
        return self.module.get_agent_run(user_context, store_id, agent_run_id)

    def list_audit_events(self, user_context: dict, store_id, **filters) -> list[dict]:
        return self.module.list_audit_events(user_context, store_id, **filters)

    @staticmethod
    def _enqueue_workflow_run(workflow_run_id: str, trace_id: str | None = None) -> None:
        from app.tasks.workflows import execute_workflow_run

        execute_workflow_run.delay(workflow_run_id, trace_id)
