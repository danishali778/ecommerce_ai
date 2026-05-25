from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is required for repository integration tests")

if TEST_DATABASE_URL:
    os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)
    os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
    os.environ.setdefault("SUPABASE_ANON_KEY", "anon")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service")

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from app.core.db import Base
    from app.repositories.idempotency_repository import IdempotencyRepository
    from app.repositories.models import Notification, Organization, Store, User
    from app.repositories.notification_repository import NotificationRepository


@pytest.fixture()
def db_session():
    engine = create_engine(TEST_DATABASE_URL, future=True, pool_pre_ping=True)
    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS commerce_ops"))
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_idempotency_repository_round_trip(db_session):
    organization = Organization(id=uuid4(), name="Org", slug=f"org-{uuid4()}", status="active")
    user = User(id=uuid4(), organization_id=organization.id, email=f"{uuid4()}@example.com", full_name="User", status="active")
    db_session.add_all([organization, user])
    db_session.commit()

    repository = IdempotencyRepository(db_session)
    record = repository.create_record(
        organization_id=organization.id,
        scope="sync:create",
        idempotency_key="idem-1",
        request_fingerprint="fingerprint",
        resource_type="sync_run",
        resource_id=uuid4(),
        response_json={"id": "sync-1"},
    )
    db_session.commit()

    loaded = repository.get_record(organization.id, "sync:create", "idem-1")

    assert loaded is not None
    assert loaded.id == record.id
    assert loaded.response_json == {"id": "sync-1"}


def test_notification_repository_filters_by_status_type_and_store(db_session):
    organization = Organization(id=uuid4(), name="Org", slug=f"org-{uuid4()}", status="active")
    user = User(id=uuid4(), organization_id=organization.id, email=f"{uuid4()}@example.com", full_name="User", status="active")
    store = Store(
        id=uuid4(),
        organization_id=organization.id,
        platform="shopify",
        name="Store",
        domain=f"{uuid4()}.example.com",
        connection_status="connected",
    )
    db_session.add_all([organization, user, store])
    db_session.flush()
    db_session.add_all(
        [
            Notification(
                id=uuid4(),
                organization_id=organization.id,
                store_id=store.id,
                user_id=user.id,
                type="approval_pending",
                channel="in_app",
                title="Pending",
                body="Needs review",
                payload_json={},
                status="unread",
            ),
            Notification(
                id=uuid4(),
                organization_id=organization.id,
                store_id=store.id,
                user_id=user.id,
                type="sync_failed",
                channel="in_app",
                title="Sync failed",
                body="Failure",
                payload_json={},
                status="read",
                read_at=datetime.now(timezone.utc),
            ),
        ]
    )
    db_session.commit()

    repository = NotificationRepository(db_session)
    results = repository.list_for_user(
        organization.id,
        user.id,
        status="unread",
        notification_type="approval_pending",
        store_id=store.id,
    )

    assert len(results) == 1
    assert results[0].type == "approval_pending"
