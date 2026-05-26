from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import SupportConversation, SupportMessage


class SupportRepository(Repository):
    def create_conversation(self, **values) -> SupportConversation:
        conversation = SupportConversation(**values)
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def list_conversations(self, organization_id: UUID, store_id: UUID, *, status: str | None = None) -> list[SupportConversation]:
        query = (
            select(SupportConversation)
            .where(
                SupportConversation.organization_id == organization_id,
                SupportConversation.store_id == store_id,
            )
            .order_by(SupportConversation.updated_at.desc())
        )
        if status:
            query = query.where(SupportConversation.status == status)
        return list(self.db.scalars(query))

    def get_conversation(self, organization_id: UUID, store_id: UUID, conversation_id: UUID) -> SupportConversation | None:
        return self.db.scalar(
            select(SupportConversation).where(
                SupportConversation.organization_id == organization_id,
                SupportConversation.store_id == store_id,
                SupportConversation.id == conversation_id,
            )
        )

    def update_conversation(self, conversation: SupportConversation, **values) -> SupportConversation:
        for key, value in values.items():
            setattr(conversation, key, value)
        self.db.flush()
        return conversation

    def create_message(self, **values) -> SupportMessage:
        message = SupportMessage(**values)
        self.db.add(message)
        self.db.flush()
        return message

    def list_messages(self, organization_id: UUID, store_id: UUID, conversation_id: UUID) -> list[SupportMessage]:
        return list(
            self.db.scalars(
                select(SupportMessage)
                .where(
                    SupportMessage.organization_id == organization_id,
                    SupportMessage.store_id == store_id,
                    SupportMessage.conversation_id == conversation_id,
                )
                .order_by(SupportMessage.created_at.asc())
            )
        )

    def get_message(self, organization_id: UUID, store_id: UUID, conversation_id: UUID, message_id: UUID) -> SupportMessage | None:
        return self.db.scalar(
            select(SupportMessage).where(
                SupportMessage.organization_id == organization_id,
                SupportMessage.store_id == store_id,
                SupportMessage.conversation_id == conversation_id,
                SupportMessage.id == message_id,
            )
        )
