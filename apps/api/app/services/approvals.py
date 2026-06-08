from app.modules.approvals import ApprovalModule
from app.core.runtime import call_with_optional_trace


class ApprovalService:
    def __init__(self, db, module: ApprovalModule | None = None) -> None:
        self.db = db
        self.module = module or ApprovalModule(db)

    def list_approvals(self, user_context: dict) -> list[dict]:
        return self.module.list_approvals(user_context)

    def get_approval(self, user_context: dict, approval_id) -> dict:
        return self.module.get_approval(user_context, approval_id)

    def approve(self, user_context: dict, approval_id, review_notes: str | None, idempotency_key: str | None, trace_id: str | None = None) -> dict:
        result = call_with_optional_trace(
            self.module.approve,
            user_context,
            approval_id,
            review_notes,
            idempotency_key,
            trace_id=trace_id,
        )
        if result.pop("_enqueue_execution", False) or result.pop("_enqueue_publish", False):
            call_with_optional_trace(self._enqueue_execution, result["id"], trace_id=trace_id)
        return result

    def reject(self, user_context: dict, approval_id, review_notes: str | None, idempotency_key: str | None) -> dict:
        return self.module.reject(user_context, approval_id, review_notes, idempotency_key)

    def cancel(self, user_context: dict, approval_id, review_notes: str | None, idempotency_key: str | None) -> dict:
        return self.module.cancel(user_context, approval_id, review_notes, idempotency_key)

    def retry_execution(self, user_context: dict, approval_id, review_notes: str | None, idempotency_key: str | None, trace_id: str | None = None) -> dict:
        result = call_with_optional_trace(
            self.module.retry_execution,
            user_context,
            approval_id,
            review_notes,
            idempotency_key,
            trace_id=trace_id,
        )
        if result.pop("_enqueue_execution", False) or result.pop("_enqueue_publish", False):
            call_with_optional_trace(self._enqueue_execution, result["id"], trace_id=trace_id)
        return result

    def execute_approval(self, approval_id: str, trace_id: str | None = None) -> dict | None:
        return call_with_optional_trace(self.module.execute_approval, approval_id, trace_id=trace_id)

    @staticmethod
    def _enqueue_execution(approval_id: str, trace_id: str | None = None) -> None:
        from app.tasks.approvals import execute_approval_task

        execute_approval_task.delay(approval_id, trace_id)
