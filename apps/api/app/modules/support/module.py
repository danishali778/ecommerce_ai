from __future__ import annotations

from typing import Any
from uuid import UUID

from app.agents.support.runner import SupportAgentRunner
from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.repositories.store_repository import StoreRepository
from app.repositories.support_repository import SupportRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.workflow_repository import WorkflowRepository


VALID_CONVERSATION_STATUSES = {"open", "pending_review", "resolved"}
VALID_MESSAGE_DIRECTIONS = {"inbound", "draft_outbound", "manual_outbound", "internal_note"}


def serialize_conversation(conversation) -> dict[str, Any]:
    return {
        "id": str(conversation.id),
        "store_id": str(conversation.store_id),
        "customer_id": str(conversation.customer_id) if conversation.customer_id else None,
        "order_id": str(conversation.order_id) if conversation.order_id else None,
        "external_ticket_id": conversation.external_ticket_id,
        "channel": conversation.channel,
        "status": conversation.status,
        "assigned_user_id": str(conversation.assigned_user_id) if conversation.assigned_user_id else None,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


def serialize_message(message) -> dict[str, Any]:
    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "direction": message.direction,
        "body": message.body,
        "generated_by_ai": message.generated_by_ai,
        "confidence_score": float(message.confidence_score) if message.confidence_score is not None else None,
        "needs_human_review": message.needs_human_review,
        "review_reason_code": message.review_reason_code,
        "status": message.status,
        "cited_policy_chunks_json": message.cited_policy_chunks_json,
        "cited_order_facts_summary": message.cited_order_facts_summary,
        "created_by_user_id": str(message.created_by_user_id) if message.created_by_user_id else None,
        "created_at": message.created_at.isoformat(),
        "updated_at": message.updated_at.isoformat(),
    }


class SupportModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.sync_repository = SyncRepository(db)
        self.support_repository = SupportRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.agent_runner = SupportAgentRunner(db)

    def create_conversation(self, user_context: dict, store_id: UUID, payload) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.SUPPORT_WRITE)
        if payload.customer_id:
            customer = self.sync_repository.get_customer(organization_id, store_id, payload.customer_id)
            if customer is None:
                raise AppError(code="not_found", message="Customer not found", status_code=404)
        if payload.order_id:
            order = self.sync_repository.get_order(organization_id, store_id, payload.order_id)
            if order is None:
                raise AppError(code="not_found", message="Order not found", status_code=404)
        conversation = self.support_repository.create_conversation(
            organization_id=organization_id,
            store_id=store_id,
            customer_id=payload.customer_id,
            order_id=payload.order_id,
            external_ticket_id=payload.external_ticket_id,
            channel=payload.channel,
            status="open",
            assigned_user_id=payload.assigned_user_id,
        )
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="support_conversation",
            entity_id=conversation.id,
            action_type="create",
            source_type="api",
            outcome="succeeded",
            metadata_json={"channel": conversation.channel},
        )
        self.db.commit()
        return serialize_conversation(conversation)

    def list_conversations(self, user_context: dict, store_id: UUID, *, status: str | None = None) -> list[dict]:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.SUPPORT_READ)
        conversations = self.support_repository.list_conversations(organization_id, store_id, status=status)
        return [serialize_conversation(item) for item in conversations]

    def get_conversation(self, user_context: dict, store_id: UUID, conversation_id: UUID) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.SUPPORT_READ)
        conversation = self.support_repository.get_conversation(organization_id, store_id, conversation_id)
        if conversation is None:
            raise AppError(code="not_found", message="Support conversation not found", status_code=404)
        return serialize_conversation(conversation)

    def update_conversation_status(self, user_context: dict, store_id: UUID, conversation_id: UUID, status: str) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.SUPPORT_WRITE)
        if status not in VALID_CONVERSATION_STATUSES:
            raise AppError(code="validation_error", message="Unsupported support conversation status", status_code=422)
        conversation = self.support_repository.get_conversation(organization_id, store_id, conversation_id)
        if conversation is None:
            raise AppError(code="not_found", message="Support conversation not found", status_code=404)
        self.support_repository.update_conversation(conversation, status=status)
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="support_conversation",
            entity_id=conversation.id,
            action_type="status_update",
            source_type="api",
            outcome="succeeded",
            metadata_json={"status": status},
        )
        self.db.commit()
        return serialize_conversation(conversation)

    def create_message(self, user_context: dict, store_id: UUID, conversation_id: UUID, payload) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.SUPPORT_WRITE)
        if payload.direction not in VALID_MESSAGE_DIRECTIONS:
            raise AppError(code="validation_error", message="Unsupported support message direction", status_code=422)
        conversation = self.support_repository.get_conversation(organization_id, store_id, conversation_id)
        if conversation is None:
            raise AppError(code="not_found", message="Support conversation not found", status_code=404)
        message = self.support_repository.create_message(
            organization_id=organization_id,
            store_id=store_id,
            conversation_id=conversation_id,
            direction=payload.direction,
            body=payload.body,
            generated_by_ai=False,
            confidence_score=None,
            needs_human_review=False,
            review_reason_code=None,
            status="logged" if payload.direction == "inbound" else "resolved",
            cited_policy_chunks_json=[],
            cited_order_facts_summary=None,
            created_by_user_id=UUID(user_context["user"]["id"]),
        )
        if payload.direction == "inbound":
            self.support_repository.update_conversation(conversation, status="open")
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="support_message",
            entity_id=message.id,
            action_type="create",
            source_type="api",
            outcome="succeeded",
            metadata_json={"direction": message.direction},
        )
        self.db.commit()
        return serialize_message(message)

    def list_messages(self, user_context: dict, store_id: UUID, conversation_id: UUID) -> list[dict]:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.SUPPORT_READ)
        conversation = self.support_repository.get_conversation(organization_id, store_id, conversation_id)
        if conversation is None:
            raise AppError(code="not_found", message="Support conversation not found", status_code=404)
        return [serialize_message(message) for message in self.support_repository.list_messages(organization_id, store_id, conversation_id)]

    def generate_reply_draft(self, user_context: dict, store_id: UUID, conversation_id: UUID, payload, trace_id: str | None = None) -> dict:
        del payload
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.SUPPORT_GENERATE)
        conversation = self.support_repository.get_conversation(organization_id, store_id, conversation_id)
        if conversation is None:
            raise AppError(code="not_found", message="Support conversation not found", status_code=404)
        result = self.agent_runner.start_generation(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            conversation=conversation,
            trace_id=trace_id,
        )
        self.db.commit()
        result["_enqueue_generation"] = True
        return result

    def require_store_access(self, user_context: dict, store_id: UUID) -> UUID:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        organization_id = UUID(organization["id"])
        store = self.store_repository.get_store(organization_id, store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return organization_id
