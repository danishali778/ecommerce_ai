from unittest.mock import Mock
from unittest.mock import patch

from app.services.catalog import CatalogService


def test_generate_draft_enqueues_background_generation_when_requested():
    db = Mock()
    module = Mock()
    module.generate_draft.return_value = {
        "workflow_run_id": "workflow-1",
        "agent_run_id": "agent-1",
        "status": "queued",
        "_enqueue_generation": True,
    }
    service = CatalogService(db=db, module=module)
    user_context = {"user": {"id": "u1"}, "organization": {"id": "o1"}}

    with patch.object(service, "_enqueue_generation") as enqueue_mock:
        result = service.generate_draft(user_context, "store-1", "product-1", Mock())

    assert result["agent_run_id"] == "agent-1"
    module.generate_draft.assert_called_once()
    enqueue_mock.assert_called_once_with("agent-1")
