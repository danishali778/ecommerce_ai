from app.modules.workflows import WorkflowModule
from app.core.runtime import call_with_optional_trace


class WorkflowService:
    def __init__(self, db, module: WorkflowModule | None = None) -> None:
        self.db = db
        self.module = module or WorkflowModule(db)

    def list_workflows(self, user_context: dict, store_id):
        return self.module.list_workflows(user_context, store_id)

    def create_workflow(self, user_context: dict, store_id, payload):
        return self.module.create_workflow(user_context, store_id, payload)

    def get_workflow(self, user_context: dict, store_id, workflow_id):
        return self.module.get_workflow(user_context, store_id, workflow_id)

    def update_workflow(self, user_context: dict, store_id, workflow_id, payload):
        return self.module.update_workflow(user_context, store_id, workflow_id, payload)

    def delete_workflow(self, user_context: dict, store_id, workflow_id):
        return self.module.delete_workflow(user_context, store_id, workflow_id)

    def enable_workflow(self, user_context: dict, store_id, workflow_id):
        return self.module.enable_workflow(user_context, store_id, workflow_id)

    def disable_workflow(self, user_context: dict, store_id, workflow_id):
        return self.module.disable_workflow(user_context, store_id, workflow_id)

    def test_workflow(self, user_context: dict, store_id, workflow_id, payload):
        return self.module.test_workflow(user_context, store_id, workflow_id, payload)

    def evaluate_event(self, *, organization_id, store_id, trigger_type: str, entity_type: str, entity_id, payload: dict, trace_id: str | None = None):
        return call_with_optional_trace(
            self.module.evaluate_event,
            organization_id=organization_id,
            store_id=store_id,
            trigger_type=trigger_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            trace_id=trace_id,
        )

    def execute_workflow_run(self, workflow_run_id: str, trace_id: str | None = None):
        return call_with_optional_trace(self.module.execute_workflow_run, workflow_run_id, trace_id=trace_id)
