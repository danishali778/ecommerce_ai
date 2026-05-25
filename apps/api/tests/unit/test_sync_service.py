from unittest.mock import Mock, patch

from app.services.sync import SyncService


def test_create_sync_run_delegates_and_enqueues():
    db = Mock()
    module = Mock()
    module.create_sync_run.return_value = {"id": "sync-run-1", "status": "queued", "_enqueue_sync_run": True}
    service = SyncService(db=db, module=module)
    user_context = {"user": {"id": "u1"}, "organization": {"id": "o1"}}

    with patch.object(service, "_enqueue_sync_run") as enqueue_mock:
        result = service.create_sync_run(user_context, "store-1", "manual_full", "idem-1")

    assert result["id"] == "sync-run-1"
    module.create_sync_run.assert_called_once_with(user_context, "store-1", "manual_full", "idem-1")
    enqueue_mock.assert_called_once_with("sync-run-1")


def test_create_sync_run_does_not_enqueue_idempotent_replay():
    db = Mock()
    module = Mock()
    module.create_sync_run.return_value = {"id": "sync-run-1", "status": "queued"}
    service = SyncService(db=db, module=module)
    user_context = {"user": {"id": "u1"}, "organization": {"id": "o1"}}

    with patch.object(service, "_enqueue_sync_run") as enqueue_mock:
        result = service.create_sync_run(user_context, "store-1", "manual_full", "idem-1")

    assert result["id"] == "sync-run-1"
    enqueue_mock.assert_not_called()
