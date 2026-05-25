from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import uuid4

import httpx
import pytest


@dataclass
class LiveContext:
    base_url: str
    access_token: str
    organization_id: str
    store_id: str


def _base_url() -> str:
    return os.getenv("LIVE_API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _json(response: httpx.Response) -> dict:
    response.raise_for_status()
    return response.json()


@pytest.fixture(scope="session")
def live_client() -> httpx.Client:
    return httpx.Client(base_url=_base_url(), timeout=30.0, follow_redirects=False)


@pytest.fixture(scope="session")
def live_context(live_client: httpx.Client) -> LiveContext:
    email = os.getenv("LIVE_TEST_EMAIL", f"live-{uuid4().hex[:10]}@example.com")
    password = os.getenv("LIVE_TEST_PASSWORD", "LiveTestPass123!")
    full_name = os.getenv("LIVE_TEST_FULL_NAME", "Live Test User")
    register = live_client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    register_payload = _json(register)["data"]
    access_token = register_payload["access_token"]

    me = _json(live_client.get("/auth/me", headers=_auth_headers(access_token)))["data"]
    if me["organization"] is None:
        organization = _json(
            live_client.post(
                "/organizations",
                headers=_auth_headers(access_token),
                json={
                    "name": f"Live Org {uuid4().hex[:6]}",
                    "slug": f"live-org-{uuid4().hex[:8]}",
                },
            )
        )["data"]
        organization_id = str(organization["id"])
    else:
        organization_id = str(me["organization"]["id"])

    store = _json(
        live_client.post(
            "/stores",
            headers=_auth_headers(access_token),
            json={
                "name": f"Live Store {uuid4().hex[:6]}",
                "platform": "shopify",
                "domain": os.getenv("LIVE_TEST_STORE_DOMAIN", f"live-{uuid4().hex[:8]}.myshopify.com"),
                "currency": "USD",
                "timezone": "UTC",
            },
        )
    )["data"]

    return LiveContext(
        base_url=_base_url(),
        access_token=access_token,
        organization_id=organization_id,
        store_id=str(store["id"]),
    )


def _skip_unless_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(f"{name} is required for this live test")
    return value


@pytest.mark.live
def test_live_health_and_ready(live_client: httpx.Client):
    health = live_client.get("/healthz")
    ready = live_client.get("/readyz")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}


@pytest.mark.live
def test_live_auth_and_org_context(live_client: httpx.Client, live_context: LiveContext):
    me = _json(live_client.get("/auth/me", headers=_auth_headers(live_context.access_token)))["data"]
    current_org = _json(live_client.get("/organizations/current", headers=_auth_headers(live_context.access_token)))["data"]

    assert me["organization"] is not None
    assert me["organization"]["id"] == live_context.organization_id
    assert current_org["id"] == live_context.organization_id
    assert "permissions" in me
    assert "roles" in me


@pytest.mark.live
def test_live_auth_login_refresh_logout(live_client: httpx.Client):
    email = os.getenv("LIVE_TEST_LOGIN_EMAIL") or f"login-{uuid4().hex[:10]}@example.com"
    password = os.getenv("LIVE_TEST_LOGIN_PASSWORD") or "LiveLoginPass123!"
    full_name = "Live Login User"

    register = _json(
        live_client.post(
            "/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
    )["data"]
    login = live_client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    assert "commerceops_refresh_token=" in login.headers.get("set-cookie", "")

    refresh_cookie = login.cookies.get("commerceops_refresh_token")
    refresh = live_client.post("/auth/refresh", cookies={"commerceops_refresh_token": refresh_cookie})
    logout = live_client.post("/auth/logout", cookies={"commerceops_refresh_token": refresh_cookie})

    assert register["access_token"]
    assert refresh.status_code == 200
    assert logout.status_code == 200
    assert logout.json()["data"]["logged_out"] is True


@pytest.mark.live
def test_live_roles_and_users_routes(live_client: httpx.Client, live_context: LiveContext):
    headers = _auth_headers(live_context.access_token)
    roles = _json(live_client.get("/roles", headers=headers))["data"]
    users_before = _json(live_client.get("/users", headers=headers))["data"]

    created = _json(
        live_client.post(
            "/users",
            headers=headers,
            json={
                "email": f"member-{uuid4().hex[:10]}@example.com",
                "full_name": "Member User",
                "role_names": ["Viewer"],
            },
        )
    )["data"]
    updated = _json(
        live_client.patch(
            f"/users/{created['id']}",
            headers=headers,
            json={"full_name": "Updated Member User", "status": "active", "role_names": ["Support Agent"]},
        )
    )["data"]
    users_after = _json(live_client.get("/users?role=Support Agent", headers=headers))["data"]

    assert any(role["name"] == "Viewer" for role in roles)
    assert isinstance(users_before, list)
    assert created["email"].endswith("@example.com")
    assert updated["full_name"] == "Updated Member User"
    assert any(user["id"] == created["id"] for user in users_after)


@pytest.mark.live
def test_live_store_sync_dashboard_notification_and_approval_routes(live_client: httpx.Client, live_context: LiveContext):
    headers = _auth_headers(live_context.access_token)
    store_id = live_context.store_id

    stores = _json(live_client.get("/stores", headers=headers))["data"]
    store = _json(live_client.get(f"/stores/{store_id}", headers=headers))["data"]
    install_url = _json(
        live_client.post(
            f"/stores/{store_id}/shopify/install-url",
            headers=headers,
            json={"redirect_uri": f"{live_context.base_url.replace('/api/v1', '')}/api/v1/shopify/callback"},
        )
    )["data"]
    integration = live_client.get(f"/stores/{store_id}/integration", headers=headers)
    sync_create = live_client.post(
        f"/stores/{store_id}/sync-runs",
        headers={**headers, "Idempotency-Key": f"sync-{uuid4().hex}"},
        json={"mode": "manual_full"},
    )
    sync_runs = _json(live_client.get(f"/stores/{store_id}/sync-runs", headers=headers))["data"]
    dashboard = _json(live_client.get(f"/stores/{store_id}/dashboard/summary", headers=headers))["data"]
    workflow_runs = _json(live_client.get(f"/stores/{store_id}/workflow-runs", headers=headers))["data"]
    agent_runs = _json(live_client.get(f"/stores/{store_id}/agent-runs", headers=headers))["data"]
    audit_events = _json(live_client.get(f"/stores/{store_id}/audit-events", headers=headers))["data"]
    approvals = _json(live_client.get("/approvals", headers=headers))["data"]
    notifications = _json(live_client.get("/notifications", headers=headers))["data"]

    assert any(item["id"] == store_id for item in stores)
    assert store["id"] == store_id
    assert install_url["install_url"].startswith("https://")
    assert "state" in install_url
    assert integration.status_code in {200, 404}
    assert sync_create.status_code == 409
    assert isinstance(sync_runs, list)
    assert "product_count" in dashboard
    assert isinstance(workflow_runs, list)
    assert isinstance(agent_runs, list)
    assert isinstance(audit_events, list)
    assert isinstance(approvals, list)
    assert isinstance(notifications, list)


@pytest.mark.live
def test_live_connected_store_read_routes(live_client: httpx.Client, live_context: LiveContext):
    connected_store_id = os.getenv("LIVE_CONNECTED_STORE_ID")
    if not connected_store_id:
        pytest.skip("LIVE_CONNECTED_STORE_ID is required for connected-store read tests")

    headers = _auth_headers(live_context.access_token)
    sync_runs = live_client.get(f"/stores/{connected_store_id}/sync-runs", headers=headers)
    products = live_client.get(f"/stores/{connected_store_id}/products", headers=headers)
    orders = live_client.get(f"/stores/{connected_store_id}/orders", headers=headers)
    customers = live_client.get(f"/stores/{connected_store_id}/customers", headers=headers)

    assert sync_runs.status_code == 200
    assert products.status_code == 200
    assert orders.status_code == 200
    assert customers.status_code == 200


@pytest.mark.live
def test_live_catalog_and_approval_routes_with_seeded_ids(live_client: httpx.Client, live_context: LiveContext):
    connected_store_id = _skip_unless_env("LIVE_CONNECTED_STORE_ID")
    product_id = _skip_unless_env("LIVE_PRODUCT_ID")
    headers = _auth_headers(live_context.access_token)

    product = live_client.get(f"/stores/{connected_store_id}/products/{product_id}", headers=headers)
    drafts = live_client.get(f"/stores/{connected_store_id}/products/{product_id}/content-drafts", headers=headers)

    assert product.status_code == 200
    assert drafts.status_code == 200


@pytest.mark.live
def test_live_generate_draft_optionally(live_client: httpx.Client, live_context: LiveContext):
    if os.getenv("LIVE_ENABLE_GENERATION") != "1":
        pytest.skip("LIVE_ENABLE_GENERATION=1 is required to run generation against the live LLM/provider")
    connected_store_id = _skip_unless_env("LIVE_CONNECTED_STORE_ID")
    product_id = _skip_unless_env("LIVE_PRODUCT_ID")

    response = live_client.post(
        f"/stores/{connected_store_id}/products/{product_id}/content-drafts/generate",
        headers=_auth_headers(live_context.access_token),
        json={
            "generation_targets": ["description", "seo", "tags"],
            "tone": "clear_and_premium",
            "constraints": {},
        },
    )

    assert response.status_code == 202
    payload = response.json()["data"]
    assert payload["workflow_run_id"]
    assert payload["agent_run_id"]
