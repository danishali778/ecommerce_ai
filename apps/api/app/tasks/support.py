from uuid import UUID

from app.core.celery_app import celery_app
from app.core.settings import get_settings
from app.repositories.models import AgentRun
from app.services.support import SupportService
from app.tasks.runtime import execute_tracked_task


@celery_app.task(name="app.tasks.support.generate_support_reply_draft", bind=True)
def generate_support_reply_draft(self, agent_run_id: str, trace_id: str | None = None) -> None:
    settings = get_settings()

    def subject_loader(db):
        return db.get(AgentRun, UUID(agent_run_id))

    def operation(db, active_trace_id: str):
        service = SupportService(db)
        service.execute_generation(agent_run_id, trace_id=active_trace_id)

    execute_tracked_task(
        task=self,
        subject_type="agent_run",
        subject_id=UUID(agent_run_id),
        organization_id=None,
        store_id=None,
        subject_loader=subject_loader,
        operation=operation,
        max_retries=settings.agent_retry_max_retries,
        base_delay_seconds=settings.agent_retry_base_delay_seconds,
        trace_id=trace_id,
    )
