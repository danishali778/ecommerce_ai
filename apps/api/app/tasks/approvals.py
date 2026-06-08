from uuid import UUID

from app.core.celery_app import celery_app
from app.core.settings import get_settings
from app.repositories.models import ApprovalRequest
from app.services.approvals import ApprovalService
from app.tasks.runtime import execute_tracked_task


@celery_app.task(name="app.tasks.approvals.execute_approval", bind=True)
def execute_approval_task(self, approval_id: str, trace_id: str | None = None) -> None:
    settings = get_settings()

    def subject_loader(db):
        return db.get(ApprovalRequest, UUID(approval_id))

    def operation(db, active_trace_id: str):
        service = ApprovalService(db)
        service.execute_approval(approval_id, trace_id=active_trace_id)

    execute_tracked_task(
        task=self,
        subject_type="approval_request",
        subject_id=UUID(approval_id),
        organization_id=None,
        store_id=None,
        subject_loader=subject_loader,
        operation=operation,
        max_retries=settings.approval_retry_max_retries,
        base_delay_seconds=settings.approval_retry_base_delay_seconds,
        trace_id=trace_id,
    )


execute_approval_publish = execute_approval_task
