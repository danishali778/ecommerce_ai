def serialize_sync_run(sync_run) -> dict:
    return {
        "id": str(sync_run.id),
        "status": sync_run.status,
        "mode": sync_run.mode,
        "records_imported": sync_run.records_imported,
        "records_failed": sync_run.records_failed,
        "entity_counts_json": sync_run.entity_counts_json,
        "error_summary": sync_run.error_summary,
        "started_at": sync_run.started_at.isoformat() if sync_run.started_at else None,
        "completed_at": sync_run.completed_at.isoformat() if sync_run.completed_at else None,
        "retry_of_sync_run_id": str(sync_run.retry_of_sync_run_id) if sync_run.retry_of_sync_run_id else None,
        "created_at": sync_run.created_at.isoformat(),
    }

