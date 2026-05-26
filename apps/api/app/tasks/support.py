from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.services.support import SupportService


@celery_app.task(name="app.tasks.support.generate_support_reply_draft")
def generate_support_reply_draft(agent_run_id: str) -> None:
    db = SessionLocal()
    try:
        service = SupportService(db)
        service.execute_generation(agent_run_id)
    finally:
        db.close()
