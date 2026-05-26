from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.settings import get_settings


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/postgres")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service")
    get_settings.cache_clear()
    from app.core.app import create_app

    return TestClient(create_app())


def _auth_context() -> dict:
    return {
        "user": {
            "id": str(uuid4()),
            "email": "user@example.com",
            "full_name": "User",
            "status": "active",
        },
        "organization": {
            "id": str(uuid4()),
            "name": "Org",
            "slug": "org",
            "status": "active",
        },
        "roles": ["Admin"],
        "permissions": ["stores.manage"],
        "accessible_stores": [],
        "available_role_summaries": [],
    }


def test_health_and_readyz(monkeypatch):
    client = _build_client(monkeypatch)
    from app.api.deps.db import get_db

    class FakeSession:
        def execute(self, query):
            self.query = str(query)

    client.app.dependency_overrides[get_db] = lambda: FakeSession()

    health = client.get("/api/v1/healthz")
    ready = client.get("/api/v1/readyz")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}
    client.app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_auth_register_login_refresh_and_logout(monkeypatch):
    client = _build_client(monkeypatch)
    from app.api.deps.auth import get_auth_service

    class FakeAuthService:
        def register(self, payload):
            return {
                "access_token": "access-1",
                "refresh_token": "refresh-1",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {"id": "u1", "email": payload.email, "full_name": payload.full_name},
                "organization": None,
                "available_roles": [],
            }

        def login(self, payload):
            return {
                "access_token": "access-2",
                "refresh_token": "refresh-2",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {"id": "u1", "email": payload.email, "full_name": "User"},
                "organization": None,
                "available_roles": [],
            }

        def refresh(self, refresh_token):
            assert refresh_token == "refresh-cookie"
            return {
                "access_token": "access-3",
                "refresh_token": "refresh-3",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": None,
                "organization": None,
                "available_roles": [],
            }

        def logout(self, refresh_token):
            assert refresh_token == "refresh-cookie"

    client.app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()

    register = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "password123", "full_name": "User"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    refresh = client.post("/api/v1/auth/refresh", cookies={"commerceops_refresh_token": "refresh-cookie"})
    logout = client.post("/api/v1/auth/logout", cookies={"commerceops_refresh_token": "refresh-cookie"})

    assert register.status_code == 201
    assert register.json()["data"]["access_token"] == "access-1"
    assert "commerceops_refresh_token=" in register.headers["set-cookie"]
    assert login.status_code == 200
    assert login.json()["data"]["access_token"] == "access-2"
    assert refresh.status_code == 200
    assert refresh.json()["data"]["access_token"] == "access-3"
    assert logout.status_code == 200
    assert logout.json()["data"]["logged_out"] is True
    client.app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_organization_routes(monkeypatch):
    client = _build_client(monkeypatch)
    from app.api.deps.auth import get_current_user_context
    from app.api.routes.organizations import get_org_service

    class FakeOrgService:
        def create_initial_organization(self, user_context, payload):
            return {
                "id": str(uuid4()),
                "name": payload.name,
                "slug": payload.slug,
                "status": "active",
                "created_at": "2026-05-24T00:00:00+00:00",
                "updated_at": "2026-05-24T00:00:00+00:00",
            }

        def get_current_organization(self, user_context):
            return {
                "id": user_context["organization"]["id"],
                "name": "Org",
                "slug": "org",
                "status": "active",
                "created_at": "2026-05-24T00:00:00+00:00",
                "updated_at": "2026-05-24T00:00:00+00:00",
            }

    client.app.dependency_overrides[get_current_user_context] = _auth_context
    client.app.dependency_overrides[get_org_service] = lambda: FakeOrgService()

    created = client.post("/api/v1/organizations", json={"name": "Org", "slug": "org"}, headers={"Authorization": "Bearer test"})
    current = client.get("/api/v1/organizations/current", headers={"Authorization": "Bearer test"})

    assert created.status_code == 201
    assert created.json()["data"]["slug"] == "org"
    assert current.status_code == 200
    assert current.json()["data"]["name"] == "Org"
    client.app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_store_and_catalog_routes(monkeypatch):
    client = _build_client(monkeypatch)
    from app.api.deps.auth import get_current_user_context
    from app.api.routes.stores import get_catalog_service, get_dashboard_service, get_store_service, get_sync_service

    store_id = str(uuid4())
    product_id = str(uuid4())
    draft_id = str(uuid4())
    sync_run_id = str(uuid4())
    order_id = str(uuid4())
    customer_id = str(uuid4())
    workflow_run_id = str(uuid4())
    agent_run_id = str(uuid4())

    class FakeStoreService:
        def create_store(self, user_context, payload):
            return {
                "id": store_id,
                "name": payload.name,
                "platform": payload.platform,
                "domain": payload.domain,
                "currency": payload.currency,
                "timezone": payload.timezone,
                "connection_status": "pending",
                "last_successful_sync_at": None,
                "created_at": "2026-05-24T00:00:00+00:00",
                "updated_at": "2026-05-24T00:00:00+00:00",
            }

        def list_stores(self, user_context):
            return [self.create_store(user_context, SimpleNamespace(name="Store", platform="shopify", domain="store.myshopify.com", currency=None, timezone=None))]

        def get_store(self, user_context, requested_store_id):
            assert str(requested_store_id) == store_id
            return self.list_stores(user_context)[0]

        def generate_install_url(self, user_context, requested_store_id, redirect_uri):
            assert str(requested_store_id) == store_id
            return {"install_url": f"https://shopify.example/install?redirect={redirect_uri}", "state": "state-1"}

        def get_integration(self, user_context, requested_store_id):
            assert str(requested_store_id) == store_id
            return {"provider": "shopify", "scopes": ["read_products"], "status": "connected", "last_successful_sync_at": None}

    class FakeSyncService:
        def create_sync_run(self, user_context, requested_store_id, mode, idempotency_key):
            assert str(requested_store_id) == store_id
            assert mode == "manual_full"
            assert idempotency_key == "idem-sync"
            return {
                "id": sync_run_id,
                "status": "queued",
                "mode": mode,
                "records_imported": 0,
                "records_failed": 0,
                "entity_counts_json": {},
                "error_summary": None,
                "started_at": None,
                "completed_at": None,
                "retry_of_sync_run_id": None,
                "created_at": "2026-05-24T00:00:00+00:00",
            }

        def list_sync_runs(self, user_context, requested_store_id):
            return [self.create_sync_run(user_context, requested_store_id, "manual_full", "idem-sync")]

        def get_sync_run(self, user_context, requested_store_id, requested_sync_run_id):
            assert str(requested_sync_run_id) == sync_run_id
            return self.list_sync_runs(user_context, requested_store_id)[0]

        def retry_sync_run(self, user_context, requested_store_id, requested_sync_run_id, idempotency_key):
            assert str(requested_sync_run_id) == sync_run_id
            assert idempotency_key == "idem-retry"
            payload = self.create_sync_run(user_context, requested_store_id, "manual_full", "idem-sync")
            payload["id"] = str(uuid4())
            payload["retry_of_sync_run_id"] = sync_run_id
            return payload

    class FakeCatalogService:
        def list_products(self, user_context, requested_store_id):
            assert str(requested_store_id) == store_id
            return [
                {
                    "id": product_id,
                    "title": "Product",
                    "handle": "product",
                    "vendor": "Vendor",
                    "status": "active",
                    "seo_title": "SEO",
                    "inventory_total": 5,
                    "updated_at": "2026-05-24T00:00:00+00:00",
                }
            ]

        def get_product(self, user_context, requested_store_id, requested_product_id):
            assert str(requested_product_id) == product_id
            payload = self.list_products(user_context, requested_store_id)[0]
            payload["variants"] = [
                {
                    "id": str(uuid4()),
                    "external_variant_id": "gid://variant/1",
                    "sku": "SKU-1",
                    "title": "Default",
                    "price": "9.99",
                    "compare_at_price": None,
                    "inventory_quantity": 5,
                }
            ]
            payload["latest_draft"] = None
            return payload

        def list_drafts(self, user_context, requested_store_id, requested_product_id):
            assert str(requested_product_id) == product_id
            return [
                {
                    "id": draft_id,
                    "product_id": product_id,
                    "generated_title": "Draft",
                    "generated_description": "Description",
                    "generated_tags": ["tag"],
                    "generated_seo_title": "SEO",
                    "generated_seo_description": "SEO desc",
                    "model_name": "model",
                    "status": "draft",
                    "created_at": "2026-05-24T00:00:00+00:00",
                    "updated_at": "2026-05-24T00:00:00+00:00",
                }
            ]

        def generate_draft(self, user_context, requested_store_id, requested_product_id, payload):
            assert str(requested_product_id) == product_id
            return {"workflow_run_id": workflow_run_id, "agent_run_id": agent_run_id, "status": "queued"}

        def get_draft(self, user_context, requested_store_id, requested_product_id, requested_draft_id):
            assert str(requested_draft_id) == draft_id
            return self.list_drafts(user_context, requested_store_id, requested_product_id)[0]

        def update_draft(self, user_context, requested_store_id, requested_product_id, requested_draft_id, payload):
            assert str(requested_draft_id) == draft_id
            result = self.get_draft(user_context, requested_store_id, requested_product_id, requested_draft_id)
            result["generated_title"] = payload.generated_title or result["generated_title"]
            return result

        def submit_draft_for_approval(self, user_context, requested_store_id, requested_product_id, requested_draft_id, reason, idempotency_key):
            assert str(requested_draft_id) == draft_id
            assert idempotency_key == "idem-approval"
            return {"approval_id": str(uuid4()), "approval_status": "pending", "draft_status": "submitted_for_approval"}

        def list_orders(self, user_context, requested_store_id):
            return [{"id": order_id, "external_order_id": "1001", "status": "open", "payment_status": "paid", "fulfillment_status": "fulfilled", "total": "19.99", "currency": "USD", "created_at": "2026-05-24T00:00:00+00:00"}]

        def get_order(self, user_context, requested_store_id, requested_order_id):
            assert str(requested_order_id) == order_id
            return self.list_orders(user_context, requested_store_id)[0]

        def list_customers(self, user_context, requested_store_id):
            return [{"id": customer_id, "email": "customer@example.com", "first_name": "A", "last_name": "B", "total_orders": 2, "created_at": "2026-05-24T00:00:00+00:00"}]

        def get_customer(self, user_context, requested_store_id, requested_customer_id):
            assert str(requested_customer_id) == customer_id
            return self.list_customers(user_context, requested_store_id)[0]

    class FakeDashboardService:
        def get_summary(self, user_context, requested_store_id):
            return {
                "latest_sync_status": "succeeded",
                "latest_sync_completed_at": "2026-05-24T00:00:00+00:00",
                "product_count": 1,
                "order_count": 1,
                "customer_count": 1,
                "low_inventory_count": 0,
                "pending_approval_count": 1,
                "recent_workflow_failures": 0,
                "recent_agent_runs": 1,
            }

    client.app.dependency_overrides[get_current_user_context] = _auth_context
    client.app.dependency_overrides[get_store_service] = lambda: FakeStoreService()
    client.app.dependency_overrides[get_sync_service] = lambda: FakeSyncService()
    client.app.dependency_overrides[get_catalog_service] = lambda: FakeCatalogService()
    client.app.dependency_overrides[get_dashboard_service] = lambda: FakeDashboardService()
    headers = {"Authorization": "Bearer test"}

    assert client.post("/api/v1/stores", json={"name": "Store", "platform": "shopify", "domain": "store.myshopify.com"}, headers=headers).status_code == 201
    assert client.get("/api/v1/stores", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}", headers=headers).status_code == 200
    assert client.post(f"/api/v1/stores/{store_id}/shopify/install-url", json={"redirect_uri": "https://example.com/callback"}, headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/integration", headers=headers).status_code == 200
    assert client.post(f"/api/v1/stores/{store_id}/sync-runs", json={"mode": "manual_full"}, headers={**headers, "Idempotency-Key": "idem-sync"}).status_code == 202
    assert client.get(f"/api/v1/stores/{store_id}/sync-runs", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/sync-runs/{sync_run_id}", headers=headers).status_code == 200
    assert client.post(f"/api/v1/stores/{store_id}/sync-runs/{sync_run_id}/retry", headers={**headers, "Idempotency-Key": "idem-retry"}).status_code == 202
    assert client.get(f"/api/v1/stores/{store_id}/dashboard/summary", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/products", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/products/{product_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/products/{product_id}/content-drafts", headers=headers).status_code == 200
    assert client.post(f"/api/v1/stores/{store_id}/products/{product_id}/content-drafts/generate", json={"generation_targets": ["description"], "tone": "clear_and_premium", "constraints": {}}, headers=headers).status_code == 202
    assert client.get(f"/api/v1/stores/{store_id}/products/{product_id}/content-drafts/{draft_id}", headers=headers).status_code == 200
    assert client.patch(f"/api/v1/stores/{store_id}/products/{product_id}/content-drafts/{draft_id}", json={"generated_title": "Updated"}, headers=headers).status_code == 200
    assert client.post(f"/api/v1/stores/{store_id}/products/{product_id}/content-drafts/{draft_id}/submit-approval", json={"reason": "Looks good"}, headers={**headers, "Idempotency-Key": "idem-approval"}).status_code == 201
    assert client.get(f"/api/v1/stores/{store_id}/orders", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/orders/{order_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/customers", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/customers/{customer_id}", headers=headers).status_code == 200
    client.app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_dashboard_approval_notification_and_integration_routes(monkeypatch):
    client = _build_client(monkeypatch)
    from app.api.deps.auth import get_current_user_context
    from app.api.routes.approvals import get_approval_service
    from app.api.routes.dashboard import get_dashboard_service
    from app.api.routes.integrations import get_store_service as get_integration_store_service
    from app.api.routes.notifications import get_notification_service

    store_id = str(uuid4())
    workflow_run_id = str(uuid4())
    agent_run_id = str(uuid4())
    approval_id = str(uuid4())
    notification_id = str(uuid4())

    class FakeApprovalService:
        def _payload(self):
            return {
                "id": approval_id,
                "status": "pending",
                "action_type": "product_content_publish",
                "entity_type": "product_content_draft",
                "entity_id": str(uuid4()),
                "reasoning": "reason",
                "review_notes": None,
                "execution_status": None,
                "execution_error": None,
                "expires_at": "2026-05-24T00:00:00+00:00",
                "created_at": "2026-05-24T00:00:00+00:00",
                "updated_at": "2026-05-24T00:00:00+00:00",
            }

        def list_approvals(self, user_context):
            return [self._payload()]

        def get_approval(self, user_context, requested_approval_id):
            assert str(requested_approval_id) == approval_id
            return self._payload()

        def approve(self, user_context, requested_approval_id, review_notes, idempotency_key):
            assert idempotency_key == "idem-approve"
            return self._payload() | {"status": "approved"}

        def reject(self, user_context, requested_approval_id, review_notes, idempotency_key):
            assert idempotency_key == "idem-reject"
            return self._payload() | {"status": "rejected"}

        def cancel(self, user_context, requested_approval_id, review_notes, idempotency_key):
            assert idempotency_key == "idem-cancel"
            return self._payload() | {"status": "cancelled"}

        def retry_execution(self, user_context, requested_approval_id, review_notes, idempotency_key):
            assert idempotency_key == "idem-retry"
            return self._payload() | {"status": "approved", "execution_status": "queued"}

    class FakeDashboardService:
        def list_workflow_runs(self, user_context, requested_store_id, **filters):
            assert filters["status"] == "failed"
            assert filters["workflow_key"] == "product_content_generated"
            assert filters["trigger_type"] == "product_content_generated"
            return [{"id": workflow_run_id, "status": "failed", "trigger_type": "product_content_generated", "workflow_id": None, "created_at": "2026-05-24T00:00:00+00:00", "input_payload": {}, "output_payload": {}, "error_message": "boom"}]

        def get_workflow_run(self, user_context, requested_store_id, requested_workflow_run_id):
            assert str(requested_workflow_run_id) == workflow_run_id
            return self.list_workflow_runs(user_context, requested_store_id, status="failed", workflow_key="product_content_generated", trigger_type="product_content_generated")[0]

        def list_agent_runs(self, user_context, requested_store_id, **filters):
            assert filters["agent_type"] == "product_content"
            assert filters["status"] == "failed"
            assert str(filters["workflow_run_id"]) == workflow_run_id
            return [{"id": agent_run_id, "status": "failed", "agent_type": "product_content", "model_name": "model", "created_at": "2026-05-24T00:00:00+00:00", "workflow_run_id": workflow_run_id, "input_summary": "in", "retrieved_context_summary": "ctx", "output_summary": None, "error_message": "boom"}]

        def get_agent_run(self, user_context, requested_store_id, requested_agent_run_id):
            assert str(requested_agent_run_id) == agent_run_id
            return self.list_agent_runs(user_context, requested_store_id, agent_type="product_content", status="failed", workflow_run_id=workflow_run_id)[0]

        def list_audit_events(self, user_context, requested_store_id, **filters):
            assert filters["entity_type"] == "approval_request"
            assert filters["action_type"] == "approve"
            assert str(filters["user_id"]) == audit_user_id
            return [{"id": str(uuid4()), "entity_type": "approval_request", "action_type": "approve", "source_type": "api", "outcome": "queued", "created_at": "2026-05-24T00:00:00+00:00", "user_id": str(filters["user_id"]), "metadata_json": {}}]

    class FakeNotificationService:
        def list_notifications(self, user_context, **filters):
            assert filters["status"] == "unread"
            assert filters["notification_type"] == "approval_pending"
            return [{"id": notification_id, "type": "approval_pending", "channel": "in_app", "title": "Pending", "body": "Review", "status": "unread", "read_at": None, "created_at": "2026-05-24T00:00:00+00:00", "store_id": store_id}]

        def mark_as_read(self, user_context, requested_notification_id):
            assert str(requested_notification_id) == notification_id
            return {"id": notification_id, "type": "approval_pending", "channel": "in_app", "title": "Pending", "body": "Review", "status": "read", "read_at": "2026-05-24T00:00:00+00:00", "created_at": "2026-05-24T00:00:00+00:00", "store_id": store_id}

    class FakeIntegrationStoreService:
        def handle_callback(self, shop, code, state, hmac, query_params):
            assert shop == "store.myshopify.com"
            assert code == "code-1"
            assert state == "state-1"
            assert hmac == "hmac-1"
            assert query_params["shop"] == "store.myshopify.com"
            return {"store_id": store_id, "integration_status": "connected"}

    client.app.dependency_overrides[get_current_user_context] = _auth_context
    client.app.dependency_overrides[get_approval_service] = lambda: FakeApprovalService()
    client.app.dependency_overrides[get_dashboard_service] = lambda: FakeDashboardService()
    client.app.dependency_overrides[get_notification_service] = lambda: FakeNotificationService()
    client.app.dependency_overrides[get_integration_store_service] = lambda: FakeIntegrationStoreService()
    headers = {"Authorization": "Bearer test"}
    audit_user_id = str(uuid4())

    assert client.get("/api/v1/approvals", headers=headers).status_code == 200
    assert client.get(f"/api/v1/approvals/{approval_id}", headers=headers).status_code == 200
    assert client.post(f"/api/v1/approvals/{approval_id}/approve", json={"review_notes": "ok"}, headers={**headers, "Idempotency-Key": "idem-approve"}).status_code == 200
    assert client.post(f"/api/v1/approvals/{approval_id}/reject", json={"review_notes": "no"}, headers={**headers, "Idempotency-Key": "idem-reject"}).status_code == 200
    assert client.post(f"/api/v1/approvals/{approval_id}/cancel", json={"review_notes": "stop"}, headers={**headers, "Idempotency-Key": "idem-cancel"}).status_code == 200
    assert client.post(f"/api/v1/approvals/{approval_id}/retry-execution", json={"review_notes": "retry"}, headers={**headers, "Idempotency-Key": "idem-retry"}).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/workflow-runs?status=failed&workflow_key=product_content_generated&trigger_type=product_content_generated", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/workflow-runs/{workflow_run_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/agent-runs?agent_type=product_content&status=failed&workflow_run_id={workflow_run_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/agent-runs/{agent_run_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/audit-events?entity_type=approval_request&action_type=approve&user_id={audit_user_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/notifications?status=unread&type=approval_pending&store_id={store_id}", headers=headers).status_code == 200
    assert client.patch(f"/api/v1/notifications/{notification_id}/read", headers=headers).status_code == 200
    assert client.get("/api/v1/integrations/shopify/callback?shop=store.myshopify.com&code=code-1&state=state-1&hmac=hmac-1").status_code == 200
    client.app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_phase1_support_policy_fraud_inventory_and_analytics_routes(monkeypatch):
    client = _build_client(monkeypatch)
    from app.api.deps.auth import get_current_user_context
    from app.api.routes.analytics import get_analytics_service
    from app.api.routes.fraud import get_fraud_service
    from app.api.routes.inventory import get_inventory_service
    from app.api.routes.policies import get_policy_service
    from app.api.routes.support import get_support_service

    store_id = str(uuid4())
    conversation_id = str(uuid4())
    message_id = str(uuid4())
    policy_id = str(uuid4())
    review_id = str(uuid4())
    suggestion_id = str(uuid4())
    alert_id = str(uuid4())
    workflow_run_id = str(uuid4())
    agent_run_id = str(uuid4())

    class FakePolicyService:
        def create_document(self, user_context, requested_store_id, payload):
            assert str(requested_store_id) == store_id
            return {
                "id": policy_id,
                "store_id": store_id,
                "document_type": payload.document_type,
                "source_type": payload.source_type,
                "title": payload.title,
                "content": payload.content,
                "version": payload.version,
                "is_active": True,
                "embedding_status": "pending",
                "created_at": "2026-05-26T00:00:00+00:00",
                "updated_at": "2026-05-26T00:00:00+00:00",
            }

        def list_documents(self, user_context, requested_store_id):
            return [self.create_document(user_context, requested_store_id, SimpleNamespace(document_type="returns", source_type="manual", title="Returns", content="Returns within 30 days.", version="v1"))]

        def get_document(self, user_context, requested_store_id, requested_policy_id):
            assert str(requested_policy_id) == policy_id
            return self.list_documents(user_context, requested_store_id)[0]

        def update_document(self, user_context, requested_store_id, requested_policy_id, payload):
            response = self.get_document(user_context, requested_store_id, requested_policy_id)
            if payload.title:
                response["title"] = payload.title
            return response

    class FakeSupportService:
        def create_conversation(self, user_context, requested_store_id, payload):
            assert str(requested_store_id) == store_id
            return {
                "id": conversation_id,
                "store_id": store_id,
                "customer_id": None,
                "order_id": None,
                "external_ticket_id": payload.external_ticket_id,
                "channel": payload.channel,
                "status": "open",
                "assigned_user_id": None,
                "created_at": "2026-05-26T00:00:00+00:00",
                "updated_at": "2026-05-26T00:00:00+00:00",
            }

        def list_conversations(self, user_context, requested_store_id, status=None):
            return [self.create_conversation(user_context, requested_store_id, SimpleNamespace(external_ticket_id="ticket-1", channel="internal_console"))]

        def get_conversation(self, user_context, requested_store_id, requested_conversation_id):
            assert str(requested_conversation_id) == conversation_id
            return self.list_conversations(user_context, requested_store_id)[0]

        def update_conversation_status(self, user_context, requested_store_id, requested_conversation_id, payload):
            response = self.get_conversation(user_context, requested_store_id, requested_conversation_id)
            response["status"] = payload.status
            return response

        def create_message(self, user_context, requested_store_id, requested_conversation_id, payload):
            assert str(requested_conversation_id) == conversation_id
            return {
                "id": message_id,
                "conversation_id": conversation_id,
                "direction": payload.direction,
                "body": payload.body,
                "generated_by_ai": False,
                "confidence_score": None,
                "needs_human_review": False,
                "review_reason_code": None,
                "status": "logged",
                "cited_policy_chunks_json": [],
                "cited_order_facts_summary": None,
                "created_by_user_id": user_context["user"]["id"],
                "created_at": "2026-05-26T00:00:00+00:00",
                "updated_at": "2026-05-26T00:00:00+00:00",
            }

        def list_messages(self, user_context, requested_store_id, requested_conversation_id):
            return [self.create_message(user_context, requested_store_id, requested_conversation_id, SimpleNamespace(direction="inbound", body="Where is my order?"))]

        def generate_reply_draft(self, user_context, requested_store_id, requested_conversation_id, payload):
            assert str(requested_conversation_id) == conversation_id
            return {"workflow_run_id": workflow_run_id, "agent_run_id": agent_run_id, "status": "queued"}

    class FakeFraudService:
        def get_order_risk_score(self, user_context, requested_store_id, requested_order_id):
            return {"order_id": str(requested_order_id), "risk_score": 65, "risk_status": "high_risk"}

        def list_risk_reviews(self, user_context, requested_store_id, risk_status=None):
            return [self.get_risk_review(user_context, requested_store_id, review_id)]

        def get_risk_review(self, user_context, requested_store_id, requested_review_id):
            assert str(requested_review_id) == review_id
            return {
                "id": review_id,
                "order_id": str(uuid4()),
                "risk_score": 65,
                "risk_status": "pending_review",
                "reason_codes_json": ["billing_shipping_country_mismatch"],
                "decision": None,
                "decision_notes": None,
                "reviewed_by_user_id": None,
                "reviewed_at": None,
                "created_at": "2026-05-26T00:00:00+00:00",
                "updated_at": "2026-05-26T00:00:00+00:00",
            }

        def record_decision(self, user_context, requested_store_id, requested_review_id, payload):
            response = self.get_risk_review(user_context, requested_store_id, requested_review_id)
            response["decision"] = payload.decision
            response["decision_notes"] = payload.decision_notes
            response["risk_status"] = "reviewed"
            response["reviewed_by_user_id"] = user_context["user"]["id"]
            response["reviewed_at"] = "2026-05-26T00:00:00+00:00"
            return response

    class FakeInventoryService:
        def list_alerts(self, user_context, requested_store_id, status=None):
            return [
                {
                    "id": alert_id,
                    "product_id": str(uuid4()),
                    "variant_id": str(uuid4()),
                    "threshold_value": 5,
                    "current_quantity": 2,
                    "status": "open",
                    "resolved_at": None,
                    "created_at": "2026-05-26T00:00:00+00:00",
                    "updated_at": "2026-05-26T00:00:00+00:00",
                }
            ]

        def list_reorder_suggestions(self, user_context, requested_store_id, status=None):
            return [self.get_reorder_suggestion(user_context, requested_store_id, suggestion_id)]

        def get_reorder_suggestion(self, user_context, requested_store_id, requested_suggestion_id):
            assert str(requested_suggestion_id) == suggestion_id
            return {
                "id": suggestion_id,
                "inventory_alert_id": alert_id,
                "product_id": str(uuid4()),
                "variant_id": str(uuid4()),
                "recommended_quantity": 13,
                "current_quantity": 2,
                "threshold_value": 5,
                "rationale_json": {"method": "deterministic_threshold_buffer"},
                "status": "open",
                "created_at": "2026-05-26T00:00:00+00:00",
                "updated_at": "2026-05-26T00:00:00+00:00",
                "supplier_draft": None,
            }

        def create_or_refresh_supplier_draft(self, user_context, requested_store_id, requested_suggestion_id, payload):
            response = self.get_reorder_suggestion(user_context, requested_store_id, requested_suggestion_id)
            response["supplier_draft"] = {
                "id": str(uuid4()),
                "vendor_name": payload.vendor_name or "Supplier",
                "recipient_email": payload.recipient_email,
                "subject": payload.subject or "Subject",
                "body": payload.body or "Body",
                "status": "draft",
                "created_by_user_id": user_context["user"]["id"],
                "created_at": "2026-05-26T00:00:00+00:00",
                "updated_at": "2026-05-26T00:00:00+00:00",
            }
            return response

    class FakeAnalyticsService:
        def get_overview(self, user_context, requested_store_id, date_from=None, date_to=None):
            return {
                "range": {"date_from": "2026-04-26T00:00:00+00:00", "date_to": "2026-05-26T00:00:00+00:00"},
                "generated_at": "2026-05-26T00:00:00+00:00",
                "sections": {
                    "sales": {"order_count": 1, "gross_sales_total": "19.99", "average_order_value": "19.99"},
                    "inventory": {"open_low_stock_alert_count": 1, "open_reorder_suggestion_count": 1},
                    "support": {"open_conversation_count": 1, "pending_support_review_count": 0, "support_drafts_generated_count": 1},
                    "fraud": {"high_risk_order_count": 1, "pending_risk_review_count": 1},
                    "operations": {"latest_sync_status": "succeeded", "latest_sync_completed_at": "2026-05-26T00:00:00+00:00", "pending_approval_count": 0},
                },
            }

        def get_automation(self, user_context, requested_store_id, date_from=None, date_to=None):
            return {
                "range": {"date_from": "2026-04-26T00:00:00+00:00", "date_to": "2026-05-26T00:00:00+00:00"},
                "generated_at": "2026-05-26T00:00:00+00:00",
                "sections": {
                    "automation": {
                        "workflow_runs_total": 2,
                        "workflow_failures_total": 0,
                        "agent_runs_total": 2,
                        "agent_runs_failed": 0,
                        "product_content_drafts_generated_count": 1,
                        "support_drafts_generated_count": 1,
                    }
                },
            }

    client.app.dependency_overrides[get_current_user_context] = _auth_context
    client.app.dependency_overrides[get_policy_service] = lambda: FakePolicyService()
    client.app.dependency_overrides[get_support_service] = lambda: FakeSupportService()
    client.app.dependency_overrides[get_fraud_service] = lambda: FakeFraudService()
    client.app.dependency_overrides[get_inventory_service] = lambda: FakeInventoryService()
    client.app.dependency_overrides[get_analytics_service] = lambda: FakeAnalyticsService()
    headers = {"Authorization": "Bearer test"}

    assert client.post(f"/api/v1/stores/{store_id}/policies", json={"document_type": "returns", "source_type": "manual", "title": "Returns", "content": "Returns within 30 days.", "version": "v1"}, headers=headers).status_code == 201
    assert client.get(f"/api/v1/stores/{store_id}/policies", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/policies/{policy_id}", headers=headers).status_code == 200
    assert client.patch(f"/api/v1/stores/{store_id}/policies/{policy_id}", json={"title": "Updated Returns"}, headers=headers).status_code == 200
    assert client.post(f"/api/v1/stores/{store_id}/support/conversations", json={"external_ticket_id": "ticket-1", "channel": "internal_console"}, headers=headers).status_code == 201
    assert client.get(f"/api/v1/stores/{store_id}/support/conversations", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/support/conversations/{conversation_id}", headers=headers).status_code == 200
    assert client.patch(f"/api/v1/stores/{store_id}/support/conversations/{conversation_id}", json={"status": "pending_review"}, headers=headers).status_code == 200
    assert client.post(f"/api/v1/stores/{store_id}/support/conversations/{conversation_id}/messages", json={"direction": "inbound", "body": "Where is my order?"}, headers=headers).status_code == 201
    assert client.get(f"/api/v1/stores/{store_id}/support/conversations/{conversation_id}/messages", headers=headers).status_code == 200
    assert client.post(f"/api/v1/stores/{store_id}/support/conversations/{conversation_id}/reply-drafts/generate", json={}, headers=headers).status_code == 202
    assert client.get(f"/api/v1/stores/{store_id}/orders/{uuid4()}/risk-score", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/risk-reviews", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/risk-reviews/{review_id}", headers=headers).status_code == 200
    assert client.post(f"/api/v1/stores/{store_id}/risk-reviews/{review_id}/decision", json={"decision": "approved", "decision_notes": "Looks safe"}, headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/inventory/alerts", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/inventory/reorder-suggestions", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/inventory/reorder-suggestions/{suggestion_id}", headers=headers).status_code == 200
    assert client.post(f"/api/v1/stores/{store_id}/inventory/reorder-suggestions/{suggestion_id}/supplier-drafts", json={"vendor_name": "Supplier"}, headers=headers).status_code == 201
    assert client.get(f"/api/v1/stores/{store_id}/analytics/overview", headers=headers).status_code == 200
    assert client.get(f"/api/v1/stores/{store_id}/analytics/automation", headers=headers).status_code == 200
    client.app.dependency_overrides.clear()
    get_settings.cache_clear()
