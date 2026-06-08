def serialize_sync_run(sync_run) -> dict:
    return {
        "id": str(sync_run.id),
        "status": sync_run.status,
        "mode": sync_run.mode,
        "records_imported": sync_run.records_imported,
        "records_failed": sync_run.records_failed,
        "entity_counts_json": sync_run.entity_counts_json,
        "error_summary": sync_run.error_summary,
        "trace_id": sync_run.trace_id,
        "failure_class": sync_run.failure_class,
        "failure_code": sync_run.failure_code,
        "last_error_at": sync_run.last_error_at.isoformat() if sync_run.last_error_at else None,
        "next_retry_at": sync_run.next_retry_at.isoformat() if sync_run.next_retry_at else None,
        "max_retries": sync_run.max_retries,
        "attempt_count": sync_run.attempt_count,
        "started_at": sync_run.started_at.isoformat() if sync_run.started_at else None,
        "completed_at": sync_run.completed_at.isoformat() if sync_run.completed_at else None,
        "retry_of_sync_run_id": str(sync_run.retry_of_sync_run_id) if sync_run.retry_of_sync_run_id else None,
        "created_at": sync_run.created_at.isoformat(),
    }

