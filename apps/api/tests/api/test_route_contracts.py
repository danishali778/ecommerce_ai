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
