from unittest.mock import Mock
from unittest.mock import patch

from app.services.approvals import ApprovalService


def test_approve_delegates_to_module_and_enqueues_when_requested():
    db = Mock()
    module = Mock()
    module.approve.return_value = {"id": "approval-1", "status": "approved", "_enqueue_execution": True}
    service = ApprovalService(db=db, module=module)
    user_context = {"user": {"id": "u1"}, "organization": {"id": "o1"}}

    with patch.object(service, "_enqueue_execution") as enqueue_mock:
        result = service.approve(user_context, "approval-1", "done", "idem-1")

    assert result["status"] == "approved"
    module.approve.assert_called_once_with(user_context, "approval-1", "done", "idem-1")
    enqueue_mock.assert_called_once_with("approval-1")


def test_retry_execution_delegates_to_module_and_enqueues_when_requested():
    db = Mock()
    module = Mock()
    module.retry_execution.return_value = {"id": "approval-2", "status": "approved", "_enqueue_execution": True}
    service = ApprovalService(db=db, module=module)
    user_context = {"user": {"id": "u1"}, "organization": {"id": "o1"}}

    with patch.object(service, "_enqueue_execution") as enqueue_mock:
        result = service.retry_execution(user_context, "approval-2", "retry", "idem-2")

    assert result["status"] == "approved"
    module.retry_execution.assert_called_once_with(user_context, "approval-2", "retry", "idem-2")
    enqueue_mock.assert_called_once_with("approval-2")
