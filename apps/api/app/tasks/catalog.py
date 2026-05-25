from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.services.catalog import CatalogService


@celery_app.task(name="app.tasks.catalog.generate_product_content_draft")
def generate_product_content_draft(agent_run_id: str) -> None:
    db = SessionLocal()
    try:
        service = CatalogService(db)
        service.module.agent_runner.execute_generation(agent_run_id)
    finally:
        db.close()
