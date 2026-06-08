from uuid import UUID

from app.core.celery_app import celery_app
from app.core.settings import get_settings
from app.repositories.models import WorkflowRun
from app.services.workflows import WorkflowService
from app.tasks.runtime import execute_tracked_task


@celery_app.task(name="app.tasks.workflows.evaluate_store_workflows", bind=True)
def evaluate_store_workflows(
    self,
    organization_id: str,
    store_id: str,
    trigger_type: str,
    entity_type: str,
    entity_id: str | None,
    payload: dict,
    event_id: str,
    trace_id: str | None = None,
) -> None:
    settings = get_settings()

    def operation(db, active_trace_id: str):
        service = WorkflowService(db)
        service.evaluate_event(
            organization_id=UUID(organization_id),
            store_id=UUID(store_id),
            trigger_type=trigger_type,
            entity_type=entity_type,
            entity_id=UUID(entity_id) if entity_id else None,
            payload=payload,
            trace_id=active_trace_id,
        )

    execute_tracked_task(
        task=self,
        subject_type="workflow_event",
        subject_id=UUID(event_id),
        organization_id=UUID(organization_id),
        store_id=UUID(store_id),
        subject_loader=None,
        operation=operation,
        max_retries=settings.workflow_retry_max_retries,
        base_delay_seconds=settings.workflow_retry_base_delay_seconds,
        trace_id=trace_id,
    )


@celery_app.task(name="app.tasks.workflows.execute_workflow_run", bind=True)
def execute_workflow_run(self, workflow_run_id: str, trace_id: str | None = None) -> None:
    settings = get_settings()

    def subject_loader(db):
        return db.get(WorkflowRun, UUID(workflow_run_id))

    def operation(db, active_trace_id: str):
        service = WorkflowService(db)
        service.execute_workflow_run(workflow_run_id, trace_id=active_trace_id)

    execute_tracked_task(
        task=self,
        subject_type="workflow_run",
        subject_id=UUID(workflow_run_id),
        organization_id=None,
        store_id=None,
        subject_loader=subject_loader,
        operation=operation,
        max_retries=settings.workflow_retry_max_retries,
        base_delay_seconds=settings.workflow_retry_base_delay_seconds,
        trace_id=trace_id,
    )
