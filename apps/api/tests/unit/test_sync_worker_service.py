from unittest.mock import Mock, patch

from app.services.sync import SyncService


def test_schedule_all_store_syncs_enqueues_each_sync_run():
    db = Mock()
    module = Mock()
    module.schedule_all_store_syncs.return_value = ["sync-1", "sync-2"]
    service = SyncService(db=db, module=module)

    with patch.object(service, "_enqueue_sync_run") as enqueue_mock:
        service.schedule_all_store_syncs()

    module.schedule_all_store_syncs.assert_called_once_with()
    enqueue_mock.assert_any_call("sync-1")
    enqueue_mock.assert_any_call("sync-2")
    assert enqueue_mock.call_count == 2
