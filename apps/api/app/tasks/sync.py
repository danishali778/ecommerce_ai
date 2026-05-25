from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.core.errors import TransientUpstreamError
from app.services.sync import SyncService


@celery_app.task(
    name="app.tasks.sync.run_store_sync",
    autoretry_for=(TransientUpstreamError,),
    retry_backoff=True,
    max_retries=3,
)
def run_store_sync(sync_run_id: str) -> None:
    db = SessionLocal()
    try:
        service = SyncService(db)
        service.execute_sync_run(sync_run_id)
    finally:
        db.close()


@celery_app.task(name="app.tasks.sync.schedule_all_store_syncs")
def schedule_all_store_syncs() -> None:
    db = SessionLocal()
    try:
        service = SyncService(db)
        service.schedule_all_store_syncs()
    finally:
        db.close()
