from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from app.core.db import SessionLocal
from app.core.runtime import calculate_next_retry_at, classify_exception
from app.repositories.runtime_repository import RuntimeRepository


logger = logging.getLogger(__name__)


SubjectLoader = Callable[[object], object | None]
Operation = Callable[[object, str], object]


def _set_attrs(subject, **values) -> None:
    for key, value in values.items():
        if hasattr(subject, key):
            setattr(subject, key, value)


def execute_tracked_task(
    *,
    task,
    subject_type: str,
    subject_id: UUID,
    organization_id: UUID | None,
    store_id: UUID | None,
    subject_loader: SubjectLoader | None,
    operation: Operation,
    max_retries: int,
    base_delay_seconds: int,
    trace_id: str | None = None,
):
    db = SessionLocal()
    runtime_repository = RuntimeRepository(db)
    attempt_started_at = datetime.now(timezone.utc)
    active_trace_id = trace_id or getattr(task.request, "id", None) or str(subject_id)

    subject = subject_loader(db) if subject_loader else None
    if subject is not None:
        organization_id = organization_id or getattr(subject, "organization_id", None)
        store_id = store_id or getattr(subject, "store_id", None)
    next_attempt_number = 1
    if subject is not None:
        next_attempt_number = int(getattr(subject, "attempt_count", 0) or 0) + 1
        _set_attrs(
            subject,
            trace_id=active_trace_id,
            max_retries=max_retries,
            attempt_count=next_attempt_number,
            next_retry_at=None,
            terminal_failed_at=None,
        )
        db.flush()

    attempt = runtime_repository.create_job_attempt(
        organization_id=organization_id,
        store_id=store_id,
        subject_type=subject_type,
        subject_id=subject_id,
        attempt_number=next_attempt_number,
        status="running",
        failure_class=None,
        failure_code=None,
        error_message=None,
        trace_id=active_trace_id,
        scheduled_retry_at=None,
        duration_ms=None,
        started_at=attempt_started_at,
        finished_at=None,
        created_at=attempt_started_at,
    )
    db.commit()

    try:
        result = operation(db, active_trace_id)
        subject = subject_loader(db) if subject_loader else None
        if subject is not None:
            _set_attrs(
                subject,
                trace_id=active_trace_id,
                failure_class=None,
                failure_code=None,
                last_error_at=None,
                next_retry_at=None,
                max_retries=max_retries,
                terminal_failed_at=None,
            )
        finished_at = datetime.now(timezone.utc)
        runtime_repository.update_job_attempt(
            attempt,
            status="succeeded",
            finished_at=finished_at,
            duration_ms=runtime_repository.duration_ms(attempt_started_at, finished_at),
        )
        db.commit()
        logger.info("runtime task succeeded", extra={"subject_type": subject_type, "subject_id": str(subject_id), "trace_id": active_trace_id})
        return result
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        failure = classify_exception(exc)
        current_retries = int(getattr(task.request, "retries", 0) or 0)
        should_retry = failure.retryable and current_retries < max_retries
        scheduled_retry_at = calculate_next_retry_at(retry_count=current_retries, base_delay_seconds=base_delay_seconds) if should_retry else None

        subject = subject_loader(db) if subject_loader else None
        if subject is not None:
            existing_retry_count = int(getattr(subject, "retry_count", 0) or 0)
            _set_attrs(
                subject,
                trace_id=active_trace_id,
                failure_class=failure.failure_class,
                failure_code=failure.failure_code,
                last_error_at=datetime.now(timezone.utc),
                next_retry_at=scheduled_retry_at,
                max_retries=max_retries,
                terminal_failed_at=None if should_retry else datetime.now(timezone.utc),
                retry_count=existing_retry_count + (1 if should_retry else 0),
            )
        finished_at = datetime.now(timezone.utc)
        runtime_repository.update_job_attempt(
            attempt,
            status="retry_scheduled" if should_retry else "failed",
            failure_class=failure.failure_class,
            failure_code=failure.failure_code,
            error_message=failure.redacted_message,
            scheduled_retry_at=scheduled_retry_at,
            finished_at=finished_at,
            duration_ms=runtime_repository.duration_ms(attempt_started_at, finished_at),
        )
        db.commit()
        logger.warning(
            "runtime task failed",
            extra={
                "subject_type": subject_type,
                "subject_id": str(subject_id),
                "trace_id": active_trace_id,
                "failure_class": failure.failure_class,
                "failure_code": failure.failure_code,
                "retryable": should_retry,
            },
        )
        if should_retry:
            countdown = max(int((scheduled_retry_at - datetime.now(timezone.utc)).total_seconds()), 1)
            raise task.retry(exc=exc, countdown=countdown)
        raise
    finally:
        db.close()
