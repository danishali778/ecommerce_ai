from unittest.mock import Mock

from app.services.dashboard import DashboardService


def test_list_workflow_runs_delegates_to_module():
    db = Mock()
    module = Mock()
    module.list_workflow_runs.return_value = [{"id": "wr-1"}]
    service = DashboardService(db=db, module=module)
    user_context = {"user": {"id": "u1"}, "organization": {"id": "o1"}}

    result = service.list_workflow_runs(user_context, "store-1")

    assert result == [{"id": "wr-1"}]
    module.list_workflow_runs.assert_called_once_with(user_context, "store-1")


def test_get_workflow_run_delegates_to_module():
    db = Mock()
    module = Mock()
    module.get_workflow_run.return_value = {"id": "wr-1"}
    service = DashboardService(db=db, module=module)
    user_context = {"user": {"id": "u1"}, "organization": {"id": "o1"}}

    result = service.get_workflow_run(user_context, "store-1", "wr-1")

    assert result == {"id": "wr-1"}
    module.get_workflow_run.assert_called_once_with(user_context, "store-1", "wr-1")
