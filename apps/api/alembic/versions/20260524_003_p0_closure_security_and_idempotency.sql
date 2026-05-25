CREATE TABLE IF NOT EXISTS commerce_ops.oauth_install_sessions (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES commerce_ops.organizations(id),
    store_id UUID NOT NULL REFERENCES commerce_ops.stores(id),
    requested_by_user_id UUID NOT NULL REFERENCES commerce_ops.users(id),
    state_nonce VARCHAR(255) NOT NULL,
    redirect_uri VARCHAR(2048) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT oauth_install_sessions_state_nonce_uidx UNIQUE (state_nonce)
);

CREATE TABLE IF NOT EXISTS commerce_ops.idempotency_records (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES commerce_ops.organizations(id)
    scope VARCHAR(255) NOT NULL,
    idempotency_key VARCHAR(255) NOT NULL,
    request_fingerprint VARCHAR(255) NULL,
    resource_type VARCHAR(100) NULL,
    resource_id UUID NULL,
    response_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT idempotency_records_scope_key_uidx UNIQUE (organization_id, scope, idempotency_key)
);

INSERT INTO commerce_ops.roles (id, name, description, created_at, updated_at)
SELECT gen_random_uuid(), 'Viewer', 'Read-only access to catalog, sync, logs, and notifications.', NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1
    FROM commerce_ops.roles
    WHERE name = 'Viewer'
);
