from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select

from app.repositories.base import Repository
from app.repositories.models import PolicyDocument, PolicyDocumentChunk


class PolicyRepository(Repository):
    def create_document(self, **values) -> PolicyDocument:
        document = PolicyDocument(**values)
        self.db.add(document)
        self.db.flush()
        return document

    def list_documents(self, organization_id: UUID, store_id: UUID) -> list[PolicyDocument]:
        return list(
            self.db.scalars(
                select(PolicyDocument)
                .where(
                    PolicyDocument.organization_id == organization_id,
                    PolicyDocument.store_id == store_id,
                    PolicyDocument.is_active.is_(True),
                )
                .order_by(PolicyDocument.document_type.asc(), PolicyDocument.updated_at.desc())
            )
        )

    def get_document(self, organization_id: UUID, store_id: UUID, policy_document_id: UUID) -> PolicyDocument | None:
        return self.db.scalar(
            select(PolicyDocument).where(
                PolicyDocument.organization_id == organization_id,
                PolicyDocument.store_id == store_id,
                PolicyDocument.id == policy_document_id,
            )
        )

    def get_document_by_type(self, organization_id: UUID, store_id: UUID, document_type: str) -> PolicyDocument | None:
        return self.db.scalar(
            select(PolicyDocument).where(
                PolicyDocument.organization_id == organization_id,
                PolicyDocument.store_id == store_id,
                PolicyDocument.document_type == document_type,
                PolicyDocument.is_active.is_(True),
            )
        )

    def update_document(self, document: PolicyDocument, **values) -> PolicyDocument:
        for key, value in values.items():
            setattr(document, key, value)
        self.db.flush()
        return document

    def replace_chunks(self, document: PolicyDocument, chunks: list[dict]) -> list[PolicyDocumentChunk]:
        self.db.execute(delete(PolicyDocumentChunk).where(PolicyDocumentChunk.policy_document_id == document.id))
        self.db.flush()
        rows: list[PolicyDocumentChunk] = []
        for chunk in chunks:
            row = PolicyDocumentChunk(
                organization_id=document.organization_id,
                store_id=document.store_id,
                policy_document_id=document.id,
                document_type=document.document_type,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                embedding_json=chunk.get("embedding_json"),
                token_count=chunk.get("token_count"),
            )
            self.db.add(row)
            rows.append(row)
        self.db.flush()
        return rows

    def list_chunks(self, organization_id: UUID, store_id: UUID, *, document_type: str | None = None) -> list[PolicyDocumentChunk]:
        query = select(PolicyDocumentChunk).where(
            PolicyDocumentChunk.organization_id == organization_id,
            PolicyDocumentChunk.store_id == store_id,
        )
        if document_type:
            query = query.where(PolicyDocumentChunk.document_type == document_type)
        query = query.order_by(PolicyDocumentChunk.document_type.asc(), PolicyDocumentChunk.chunk_index.asc())
        return list(self.db.scalars(query))

    def list_chunks_for_document(self, policy_document_id: UUID) -> list[PolicyDocumentChunk]:
        return list(
            self.db.scalars(
                select(PolicyDocumentChunk)
                .where(PolicyDocumentChunk.policy_document_id == policy_document_id)
                .order_by(PolicyDocumentChunk.chunk_index.asc())
            )
        )

