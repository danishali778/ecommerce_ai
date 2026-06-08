from uuid import UUID

from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.core.settings import get_settings
from app.repositories.models import SyncRun
from app.services.sync import SyncService
from app.tasks.runtime import execute_tracked_task


@celery_app.task(
    name="app.tasks.sync.run_store_sync",
    bind=True,
)
def run_store_sync(self, sync_run_id: str, trace_id: str | None = None) -> None:
    settings = get_settings()

    def subject_loader(db):
        return db.get(SyncRun, UUID(sync_run_id))

    def operation(db, active_trace_id: str):
        service = SyncService(db)
        service.execute_sync_run(sync_run_id, trace_id=active_trace_id)

    execute_tracked_task(
        task=self,
        subject_type="sync_run",
        subject_id=UUID(sync_run_id),
        organization_id=None,
        store_id=None,
        subject_loader=subject_loader,
        operation=operation,
        max_retries=settings.sync_retry_max_retries,
        base_delay_seconds=settings.sync_retry_base_delay_seconds,
        trace_id=trace_id,
    )


@celery_app.task(name="app.tasks.sync.schedule_all_store_syncs")
def schedule_all_store_syncs() -> None:
    db = SessionLocal()
    try:
        service = SyncService(db)
        service.schedule_all_store_syncs()
    finally:
        db.close()
