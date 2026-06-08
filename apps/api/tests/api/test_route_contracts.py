from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.settings import get_settings


def _build_client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/postgres")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service")
    get_settings.cache_clear()
    from app.core.app import create_app

    return TestClient(create_app())


def test_protected_route_requires_authentication(monkeypatch):
    client = _build_client(monkeypatch)

    response = client.get("/api/v1/notifications")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
    get_settings.cache_clear()


def test_roles_endpoint_returns_role_summaries(monkeypatch):
    client = _build_client(monkeypatch)
    from app.api.deps.auth import get_current_user_context
    from app.api.routes.users import get_user_service

    class FakeUserService:
        def list_roles(self, user_context):
            return [
                {
                    "name": "Viewer",
                    "description": "Read-only",
                    "permissions": ["catalog.read"],
                }
            ]

    client.app.dependency_overrides[get_current_user_context] = lambda: {
        "user": {"id": str(uuid4())},
        "organization": {"id": str(uuid4())},
        "permissions": ["users.manage"],
    }
    client.app.dependency_overrides[get_user_service] = lambda: FakeUserService()

    response = client.get("/api/v1/roles", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    assert response.json()["data"][0]["name"] == "Viewer"
    client.app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_auth_me_returns_permissions_payload(monkeypatch):
    client = _build_client(monkeypatch)
    from app.api.deps.auth import get_current_user_context

    client.app.dependency_overrides[get_current_user_context] = lambda: {
        "user": {"id": str(uuid4()), "email": "user@example.com", "full_name": "User", "status": "active"},
        "organization": {"id": str(uuid4()), "name": "Org", "slug": "org", "status": "active"},
        "roles": ["Viewer"],
        "permissions": ["catalog.read", "sync.read"],
        "accessible_stores": [],
        "available_role_summaries": [],
    }

    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    assert response.json()["data"]["permissions"] == ["catalog.read", "sync.read"]
    client.app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_workflow_retry_route_and_notification_delivery_routes(monkeypatch):
    client = _build_client(monkeypatch)
    from app.api.deps.auth import get_current_user_context
    from app.api.routes.dashboard import get_dashboard_service
    from app.api.routes.notification_channels import get_notification_service

    store_id = str(uuid4())
    workflow_run_id = str(uuid4())
    delivery_id = str(uuid4())
    channel_id = str(uuid4())
    notification_id = str(uuid4())

    class FakeDashboardService:
        def retry_workflow_run(self, user_context, requested_store_id, requested_workflow_run_id):
            assert str(requested_store_id) == store_id
            assert str(requested_workflow_run_id) == workflow_run_id
            return {
                "id": workflow_run_id,
                "workflow_id": str(uuid4()),
                "workflow_key": "workflow_failed",
                "trigger_type": "workflow.failed",
                "trigger_entity_type": "order",
                "trigger_entity_id": str(uuid4()),
                "status": "queued",
                "trace_id": "trace-1",
                "failure_class": None,
                "failure_code": None,
                "last_error_at": None,
                "next_retry_at": None,
                "max_retries": 3,
                "attempt_count": 1,
                "retry_count": 0,
                "terminal_failed_at": None,
                "input_payload": {},
                "output_payload": {},
                "error_message": None,
                "started_at": None,
                "completed_at": None,
                "created_at": "2026-06-08T00:00:00+00:00",
                "updated_at": "2026-06-08T00:00:00+00:00",
            }

    class FakeNotificationService:
        def list_deliveries(self, user_context, requested_store_id, status=None):
            assert str(requested_store_id) == store_id
            assert status == "failed"
            return [self.get_delivery(user_context, requested_store_id, delivery_id)]

        def get_delivery(self, user_context, requested_store_id, requested_delivery_id):
            assert str(requested_store_id) == store_id
            assert str(requested_delivery_id) == delivery_id
            return {
                "id": delivery_id,
                "notification_id": notification_id,
                "channel_id": channel_id,
                "event_type": "workflow.failed",
                "status": "failed",
                "trace_id": "trace-delivery-1",
                "failure_class": "transient",
                "failure_code": "upstream_timeout",
                "last_error": "Webhook timed out",
                "last_error_at": "2026-06-08T00:01:00+00:00",
                "next_retry_at": None,
                "max_retries": 4,
                "attempt_count": 2,
                "queued_at": "2026-06-08T00:00:00+00:00",
                "last_attempted_at": "2026-06-08T00:01:00+00:00",
                "sent_at": None,
                "created_at": "2026-06-08T00:00:00+00:00",
                "rendered_payload_json": {"title": "Workflow failed"},
                "response_payload_json": {},
            }

        def retry_delivery(self, user_context, requested_store_id, requested_delivery_id):
            payload = self.get_delivery(user_context, requested_store_id, requested_delivery_id)
            payload["status"] = "queued"
            payload["failure_class"] = None
            payload["failure_code"] = None
            payload["last_error"] = None
            return payload

    client.app.dependency_overrides[get_current_user_context] = lambda: {
        "user": {"id": str(uuid4())},
        "organization": {"id": str(uuid4())},
        "permissions": ["logs.read", "workflows.manage", "notifications.manage"],
    }
    client.app.dependency_overrides[get_dashboard_service] = lambda: FakeDashboardService()
    client.app.dependency_overrides[get_notification_service] = lambda: FakeNotificationService()
    headers = {"Authorization": "Bearer test"}

    workflow_response = client.post(
        f"/api/v1/stores/{store_id}/workflow-runs/{workflow_run_id}/retry",
        headers=headers,
    )
    assert workflow_response.status_code == 202
    assert workflow_response.json()["data"]["trace_id"] == "trace-1"

    delivery_list_response = client.get(
        f"/api/v1/stores/{store_id}/notification-deliveries",
        params={"status": "failed"},
        headers=headers,
    )
    assert delivery_list_response.status_code == 200
    assert delivery_list_response.json()["data"][0]["failure_code"] == "upstream_timeout"

    delivery_detail_response = client.get(
        f"/api/v1/stores/{store_id}/notification-deliveries/{delivery_id}",
        headers=headers,
    )
    assert delivery_detail_response.status_code == 200
    assert delivery_detail_response.json()["data"]["attempt_count"] == 2

    delivery_retry_response = client.post(
        f"/api/v1/stores/{store_id}/notification-deliveries/{delivery_id}/retry",
        headers=headers,
    )
    assert delivery_retry_response.status_code == 202
    assert delivery_retry_response.json()["data"]["status"] == "queued"

    client.app.dependency_overrides.clear()
    get_settings.cache_clear()
