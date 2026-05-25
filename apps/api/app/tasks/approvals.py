from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.services.approvals import ApprovalService


@celery_app.task(name="app.tasks.approvals.execute_approval_publish")
def execute_approval_publish(approval_id: str) -> None:
    db = SessionLocal()
    try:
        service = ApprovalService(db)
        service.execute_approval(approval_id)
    finally:
        db.close()
