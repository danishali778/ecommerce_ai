from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


SCHEMA = "commerce_ops"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    owner_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id"))
    status: Mapped[str] = mapped_column(String(50), default="active")


class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(50), default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": SCHEMA}

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id"), primary_key=True)
    role_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.roles.id"), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    assigned_by_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id"), nullable=True)


class Store(Base, TimestampMixin):
    __tablename__ = "stores"
    __table_args__ = (
        UniqueConstraint("organization_id", "domain", name="stores_org_domain_uidx"),
        {"schema": SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    platform: Mapped[str] = mapped_column(String(50), default="shopify")
    name: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(String(255))
    external_store_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    connection_status: Mapped[str] = mapped_column(String(50), default="pending")
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Integration(Base, TimestampMixin):
    __tablename__ = "integrations"
    __table_args__ = (
        UniqueConstraint("store_id", "provider", name="integrations_store_provider_uidx"),
        {"schema": SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    provider: Mapped[str] = mapped_column(String(100))
    provider_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    secret_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String()), default=list)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OauthInstallSession(Base):
    __tablename__ = "oauth_install_sessions"
    __table_args__ = (
        UniqueConstraint("state_nonce", name="oauth_install_sessions_state_nonce_uidx"),
        {"schema": SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    requested_by_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id"))
    state_nonce: Mapped[str] = mapped_column(String(255))
    redirect_uri: Mapped[str] = mapped_column(String(2048))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("organization_id", "scope", "idempotency_key", name="idempotency_records_scope_key_uidx"),
        {"schema": SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    scope: Mapped[str] = mapped_column(String(255))
    idempotency_key: Mapped[str] = mapped_column(String(255))
    request_fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SyncRun(Base):
    __tablename__ = "sync_runs"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    integration_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.integrations.id"))
    mode: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="queued")
    triggered_by_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id"), nullable=True)
    records_imported: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    entity_counts_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict, nullable=True)
    retry_of_sync_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.sync_runs.id"), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("store_id", "external_product_id", name="products_store_external_uidx"),
        {"schema": SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    external_product_id: Mapped[str] = mapped_column(String(255))
    handle: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String()), default=list)
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.sync_runs.id"), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProductVariant(Base, TimestampMixin):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("store_id", "external_variant_id", name="product_variants_store_external_uidx"),
        {"schema": SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    product_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.products.id"))
    external_variant_id: Mapped[str] = mapped_column(String(255))
    sku: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    inventory_quantity: Mapped[int] = mapped_column(Integer, default=0)
    margin_floor: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    price_ceiling: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    compare_at_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    last_sync_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.sync_runs.id"), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("store_id", "external_customer_id", name="customers_store_external_uidx"),
        {"schema": SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    external_customer_id: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    total_spend: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    total_refunds: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    last_sync_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.sync_runs.id"), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("store_id", "external_order_id", name="orders_store_external_uidx"),
        {"schema": SCHEMA},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    external_order_id: Mapped[str] = mapped_column(String(255))
    customer_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.customers.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50))
    payment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fulfillment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    billing_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipping_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    billing_postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    shipping_postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payment_attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    currency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_sync_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.sync_runs.id"), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.orders.id"))
    product_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.products.id"), nullable=True)
    variant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.product_variants.id"), nullable=True)
    external_line_item_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    total_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Workflow(Base, TimestampMixin):
    __tablename__ = "workflows"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    key: Mapped[str] = mapped_column(String(255), unique=True)
    phase_scope: Mapped[str] = mapped_column(String(32))
    trigger_type: Mapped[str] = mapped_column(String(100))
    condition_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    action_type: Mapped[str] = mapped_column(String(100))
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system_defined: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    workflow_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.workflows.id"))
    trigger_type: Mapped[str] = mapped_column(String(100))
    trigger_entity_type: Mapped[str] = mapped_column(String(100))
    trigger_entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProductContentDraft(Base, TimestampMixin):
    __tablename__ = "product_content_drafts"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    product_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.products.id"))
    source_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    generated_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generated_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_tags: Mapped[list[str]] = mapped_column(ARRAY(String()), default=list)
    generated_seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generated_seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_prompt_version: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(64), default="draft")
    submitted_approval_request_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.approval_requests.id"), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id"), nullable=True)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    agent_type: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id"), nullable=True)
    workflow_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.workflow_runs.id"), nullable=True)
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_calls_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    model_name: Mapped[str] = mapped_column(String(255))
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_usage_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_usage_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="queued")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ApprovalRequest(Base, TimestampMixin):
    __tablename__ = "approval_requests"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"))
    action_type: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    workflow_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.workflow_runs.id"), nullable=True)
    agent_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.agent_runs.id"), nullable=True)
    proposed_action_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source_snapshot_hash: Mapped[str] = mapped_column(String(255))
    source_snapshot_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reasoning: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="pending")
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    execution_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    execution_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    requested_by_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id"), nullable=True)
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_execution_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"), nullable=True)
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    action_type: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(100))
    outcome: Mapped[str] = mapped_column(String(100))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id"))
    store_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.stores.id"), nullable=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id"))
    type: Mapped[str] = mapped_column(String(100))
    channel: Mapped[str] = mapped_column(String(50), default="in_app")
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="unread")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
