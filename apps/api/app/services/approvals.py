from app.modules.approvals import ApprovalModule


class ApprovalService:
    def __init__(self, db, module: ApprovalModule | None = None) -> None:
        self.db = db
        self.module = module or ApprovalModule(db)

    def list_approvals(self, user_context: dict) -> list[dict]:
        return self.module.list_approvals(user_context)

    def get_approval(self, user_context: dict, approval_id) -> dict:
        return self.module.get_approval(user_context, approval_id)

    def approve(self, user_context: dict, approval_id, review_notes: str | None, idempotency_key: str | None) -> dict:
        result = self.module.approve(user_context, approval_id, review_notes, idempotency_key)
        if result.pop("_enqueue_publish", False):
            self._enqueue_publish(result["id"])
        return result

    def reject(self, user_context: dict, approval_id, review_notes: str | None, idempotency_key: str | None) -> dict:
        return self.module.reject(user_context, approval_id, review_notes, idempotency_key)

    def cancel(self, user_context: dict, approval_id, review_notes: str | None, idempotency_key: str | None) -> dict:
        return self.module.cancel(user_context, approval_id, review_notes, idempotency_key)

    def retry_execution(self, user_context: dict, approval_id, review_notes: str | None, idempotency_key: str | None) -> dict:
        result = self.module.retry_execution(user_context, approval_id, review_notes, idempotency_key)
        if result.pop("_enqueue_publish", False):
            self._enqueue_publish(result["id"])
        return result

    def execute_approval(self, approval_id: str) -> dict | None:
        return self.module.execute_approval(approval_id)

    @staticmethod
    def _enqueue_publish(approval_id: str) -> None:
        from app.tasks.approvals import execute_approval_publish

        execute_approval_publish.delay(approval_id)
