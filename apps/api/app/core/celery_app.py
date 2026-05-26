from celery import Celery

from app.core.settings import get_settings


settings = get_settings()

celery_app = Celery(
    "commerceops",
    broker=settings.resolved_celery_broker_url,
    backend=settings.resolved_celery_result_backend,
    include=[
        "app.tasks.sync",
        "app.tasks.catalog",
        "app.tasks.approvals",
        "app.tasks.policies",
        "app.tasks.support",
    ],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        "nightly-store-sync": {
            "task": "app.tasks.sync.schedule_all_store_syncs",
            "schedule": 60 * 60 * 24,
        }
    },
)
