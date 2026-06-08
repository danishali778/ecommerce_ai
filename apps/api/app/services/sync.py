from app.modules.sync import SyncModule
from app.core.runtime import call_with_optional_trace


class SyncService:
    def __init__(self, db, module: SyncModule | None = None) -> None:
        self.db = db
        self.module = module or SyncModule(db)

    def create_sync_run(self, user_context: dict, store_id, mode: str, idempotency_key: str | None, trace_id: str | None = None) -> dict:
        sync_run = call_with_optional_trace(
            self.module.create_sync_run,
            user_context,
            store_id,
            mode,
            idempotency_key,
            trace_id=trace_id,
        )
        if sync_run.pop("_enqueue_sync_run", False):
            call_with_optional_trace(self._enqueue_sync_run, sync_run["id"], trace_id=trace_id)
        return sync_run

    def list_sync_runs(self, user_context: dict, store_id) -> list[dict]:
        return self.module.list_sync_runs(user_context, store_id)

    def get_sync_run(self, user_context: dict, store_id, sync_run_id) -> dict:
        return self.module.get_sync_run(user_context, store_id, sync_run_id)

    def retry_sync_run(self, user_context: dict, store_id, sync_run_id, idempotency_key: str | None, trace_id: str | None = None) -> dict:
        sync_run = call_with_optional_trace(
            self.module.retry_sync_run,
            user_context,
            store_id,
            sync_run_id,
            idempotency_key,
            trace_id=trace_id,
        )
        if sync_run.pop("_enqueue_sync_run", False):
            call_with_optional_trace(self._enqueue_sync_run, sync_run["id"], trace_id=trace_id)
        return sync_run

    def execute_sync_run(self, sync_run_id: str, trace_id: str | None = None) -> None:
        call_with_optional_trace(self.module.execute_sync_run, sync_run_id, trace_id=trace_id)

    def schedule_all_store_syncs(self) -> None:
        queued_sync_run_ids = self.module.schedule_all_store_syncs()
        for sync_run_id in queued_sync_run_ids:
            self._enqueue_sync_run(sync_run_id)

    @staticmethod
    def _enqueue_sync_run(sync_run_id: str, trace_id: str | None = None) -> None:
        from app.tasks.sync import run_store_sync

        run_store_sync.delay(sync_run_id, trace_id)
