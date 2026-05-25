from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.repositories.models import Store


def generate_install_url(module, user_context: dict, store_id: UUID, redirect_uri: str) -> dict:
    require_permission(user_context, Permission.INTEGRATIONS_MANAGE)
    store = module.require_store(user_context, store_id)
    state = token_urlsafe(32)
    module.oauth_repository.create_session(
        organization_id=store.organization_id,
        store_id=store.id,
        requested_by_user_id=UUID(user_context["user"]["id"]),
        state_nonce=state,
        redirect_uri=redirect_uri,
        expires_at=datetime.now(timezone.utc) + oauth_ttl(),
    )
    install_url = module.shopify_client.build_install_url(store.domain, state=state, redirect_uri=redirect_uri)
    module.db.commit()
    return {"install_url": install_url, "state": state}


def handle_callback(module, shop: str, code: str, state: str, hmac_value: str, query_params: dict[str, str]) -> dict:
    if not module.shopify_client.verify_hmac(query_params, hmac_value):
        raise AppError(code="validation_error", message="Invalid Shopify callback HMAC", status_code=422)
    oauth_session = module.oauth_repository.get_by_state_nonce(state)
    if oauth_session is None:
        raise AppError(code="validation_error", message="Invalid Shopify callback state", status_code=422)
    now = datetime.now(timezone.utc)
    if oauth_session.used_at is not None or oauth_session.expires_at < now:
        raise AppError(code="validation_error", message="Expired or used Shopify callback state", status_code=422)
    store = module.db.query(Store).filter(Store.id == oauth_session.store_id).one_or_none()
    if store is None:
        raise AppError(code="not_found", message="Store not found for Shopify callback", status_code=404)
    if store.domain != shop:
        raise AppError(code="validation_error", message="Shopify callback shop does not match expected store", status_code=422)
    token_payload = module.shopify_client.exchange_code_for_token(shop, code)
    integration = module.store_repository.get_integration(store.id)
    scopes = token_payload.get("scope", "").split(",") if token_payload.get("scope") else []
    access_token = token_payload.get("access_token")
    if not access_token:
        raise AppError(code="upstream_error", message="Shopify token exchange returned no access token", status_code=502)
    if integration is None:
        secret_reference = module.secret_store.put(access_token)
        integration = module.store_repository.create_integration(
            organization_id=store.organization_id,
            store_id=store.id,
            provider="shopify",
            provider_account_id=shop,
            secret_reference=secret_reference,
            scopes=scopes,
            status="connected",
            last_successful_sync_at=None,
        )
    else:
        secret_reference = module.secret_store.rotate(integration.secret_reference or token_urlsafe(8), access_token)
        module.store_repository.update_integration(
            integration,
            provider_account_id=shop,
            secret_reference=secret_reference,
            scopes=scopes,
            status="connected",
        )
    module.store_repository.update_store(store, connection_status="connected")
    module.oauth_repository.mark_used(oauth_session, used_at=now)
    module.workflow_repository.create_audit_event(
        organization_id=store.organization_id,
        store_id=store.id,
        user_id=oauth_session.requested_by_user_id,
        entity_type="integration",
        entity_id=integration.id,
        action_type="shopify_connected",
        source_type="shopify_oauth",
        outcome="succeeded",
        metadata_json={"shop": shop},
    )
    module.db.commit()
    return {"store_id": str(store.id), "integration_status": "connected"}


def oauth_ttl():
    return timedelta(minutes=10)

