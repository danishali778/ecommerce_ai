from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.services.policies import PoliciesService


@celery_app.task(name="app.tasks.policies.index_policy_document")
def index_policy_document(policy_document_id: str) -> None:
    db = SessionLocal()
    try:
        service = PoliciesService(db)
        service.refresh_embeddings(policy_document_id)
    finally:
        db.close()
