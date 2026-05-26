from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.core.authz import require_any_permission, require_permission
from app.core.errors import AppError
from app.core.permissions import Permission
from app.core.settings import get_settings
from app.llm.provider import LLMProvider
from app.repositories.policy_repository import PolicyRepository
from app.repositories.models import PolicyDocument
from app.repositories.store_repository import StoreRepository
from app.repositories.workflow_repository import WorkflowRepository


SUPPORTED_POLICY_TYPES = {
    "returns",
    "shipping",
    "refunds",
    "exchange",
    "warranty",
    "cancellations",
    "general",
}


@dataclass(slots=True)
class RetrievedPolicyChunk:
    chunk_id: UUID
    document_id: UUID
    document_type: str
    chunk_index: int
    content: str
    similarity: float


def chunk_policy_content(content: str) -> list[dict[str, Any]]:
    settings = get_settings()
    chunk_size = max(settings.rag_chunk_size, 200)
    overlap = max(min(settings.rag_chunk_overlap, chunk_size // 2), 0)
    normalized = content.strip()
    if not normalized:
        return []

    chunks: list[dict[str, Any]] = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        raw_chunk = normalized[start:end].strip()
        if raw_chunk:
            chunks.append(
                {
                    "chunk_index": index,
                    "content": raw_chunk,
                    "embedding_json": None,
                    "token_count": len(raw_chunk.split()),
                }
            )
            index += 1
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks


def infer_policy_document_type(text: str) -> str | None:
    lowered = text.lower()
    keyword_map = {
        "returns": {"return", "returned", "returning"},
        "shipping": {"ship", "shipping", "delivery", "dispatch"},
        "refunds": {"refund", "refunds"},
        "exchange": {"exchange", "replace", "replacement"},
        "warranty": {"warranty", "guarantee"},
        "cancellations": {"cancel", "cancellation"},
    }
    scores = {doc_type: sum(keyword in lowered for keyword in keywords) for doc_type, keywords in keyword_map.items()}
    best = max(scores.items(), key=lambda item: item[1])
    return best[0] if best[1] > 0 else None


def lexical_overlap_score(query: str, content: str) -> float:
    query_tokens = Counter(token.lower().strip(".,!?;:()[]{}") for token in query.split() if token.strip())
    content_tokens = Counter(token.lower().strip(".,!?;:()[]{}") for token in content.split() if token.strip())
    if not query_tokens or not content_tokens:
        return 0.0
    shared = set(query_tokens).intersection(content_tokens)
    numerator = sum(min(query_tokens[token], content_tokens[token]) for token in shared)
    denominator = max(sum(query_tokens.values()), 1)
    return numerator / denominator


def retrieve_relevant_chunks(
    repository: PolicyRepository,
    llm_provider: LLMProvider,
    organization_id: UUID,
    store_id: UUID,
    query: str,
    *,
    document_type: str | None = None,
    top_k: int | None = None,
) -> list[RetrievedPolicyChunk]:
    settings = get_settings()
    chunks = repository.list_chunks(organization_id, store_id, document_type=document_type)
    if not chunks:
        return []

    query_embedding = llm_provider.generate_embedding(query)
    scored: list[RetrievedPolicyChunk] = []
    for chunk in chunks:
        similarity = 0.0
        if chunk.embedding_json:
            similarity = llm_provider.cosine_similarity(query_embedding, [float(value) for value in chunk.embedding_json])
        if similarity <= 0:
            similarity = lexical_overlap_score(query, chunk.content)
        scored.append(
            RetrievedPolicyChunk(
                chunk_id=chunk.id,
                document_id=chunk.policy_document_id,
                document_type=chunk.document_type,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                similarity=similarity,
            )
        )
    limit = top_k or settings.rag_retrieval_top_k
    scored.sort(key=lambda item: item.similarity, reverse=True)
    return [item for item in scored[:limit] if item.similarity > 0]


def serialize_document(document) -> dict[str, Any]:
    return {
        "id": str(document.id),
        "store_id": str(document.store_id),
        "document_type": document.document_type,
        "source_type": document.source_type,
        "title": document.title,
        "content": document.content,
        "version": document.version,
        "is_active": document.is_active,
        "embedding_status": document.embedding_status,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
    }


def serialize_chunk(chunk: RetrievedPolicyChunk) -> dict[str, Any]:
    return {
        "chunk_id": str(chunk.chunk_id),
        "document_id": str(chunk.document_id),
        "document_type": chunk.document_type,
        "chunk_index": chunk.chunk_index,
        "content": chunk.content,
        "similarity": round(chunk.similarity, 4),
    }


class PoliciesModule:
    def __init__(self, db) -> None:
        self.db = db
        self.store_repository = StoreRepository(db)
        self.policy_repository = PolicyRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.llm_provider = LLMProvider()

    def list_documents(self, user_context: dict, store_id: UUID) -> list[dict]:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.POLICIES_READ, Permission.POLICIES_MANAGE])
        return [serialize_document(document) for document in self.policy_repository.list_documents(organization_id, store_id)]

    def get_document(self, user_context: dict, store_id: UUID, policy_id: UUID) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_any_permission(user_context, [Permission.POLICIES_READ, Permission.POLICIES_MANAGE])
        document = self.policy_repository.get_document(organization_id, store_id, policy_id)
        if document is None:
            raise AppError(code="not_found", message="Policy document not found", status_code=404)
        return serialize_document(document)

    def create_document(self, user_context: dict, store_id: UUID, payload) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.POLICIES_MANAGE)
        document_type = payload.document_type.lower()
        if document_type not in SUPPORTED_POLICY_TYPES:
            raise AppError(code="validation_error", message="Unsupported policy document type", status_code=422)
        existing = self.policy_repository.get_document_by_type(organization_id, store_id, document_type)
        if existing is not None:
            raise AppError(code="conflict", message="Policy document already exists for this type", status_code=409)
        document = self.policy_repository.create_document(
            organization_id=organization_id,
            store_id=store_id,
            document_type=document_type,
            source_type=payload.source_type,
            title=payload.title,
            content=payload.content,
            version=payload.version,
            is_active=True,
            embedding_status="pending",
        )
        self.policy_repository.replace_chunks(document, chunk_policy_content(payload.content))
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="policy_document",
            entity_id=document.id,
            action_type="create",
            source_type="api",
            outcome="queued_for_indexing",
            metadata_json={"document_type": document.document_type},
        )
        self.db.commit()
        serialized = serialize_document(document)
        serialized["_enqueue_embedding_refresh"] = True
        return serialized

    def update_document(self, user_context: dict, store_id: UUID, policy_id: UUID, payload) -> dict:
        organization_id = self.require_store_access(user_context, store_id)
        require_permission(user_context, Permission.POLICIES_MANAGE)
        document = self.policy_repository.get_document(organization_id, store_id, policy_id)
        if document is None:
            raise AppError(code="not_found", message="Policy document not found", status_code=404)
        if payload.document_type and payload.document_type.lower() not in SUPPORTED_POLICY_TYPES:
            raise AppError(code="validation_error", message="Unsupported policy document type", status_code=422)
        updated_document_type = payload.document_type.lower() if payload.document_type else document.document_type
        sibling = self.policy_repository.get_document_by_type(organization_id, store_id, updated_document_type)
        if sibling is not None and sibling.id != document.id:
            raise AppError(code="conflict", message="Policy document already exists for this type", status_code=409)
        self.policy_repository.update_document(
            document,
            document_type=updated_document_type,
            source_type=payload.source_type or document.source_type,
            title=payload.title or document.title,
            content=payload.content or document.content,
            version=payload.version if payload.version is not None else document.version,
            embedding_status="pending",
        )
        self.policy_repository.replace_chunks(document, chunk_policy_content(document.content))
        self.workflow_repository.create_audit_event(
            organization_id=organization_id,
            store_id=store_id,
            user_id=UUID(user_context["user"]["id"]),
            entity_type="policy_document",
            entity_id=document.id,
            action_type="update",
            source_type="api",
            outcome="queued_for_indexing",
            metadata_json={"document_type": document.document_type},
        )
        self.db.commit()
        serialized = serialize_document(document)
        serialized["_enqueue_embedding_refresh"] = True
        return serialized

    def refresh_embeddings(self, policy_document_id: str) -> None:
        document = self.db.get(PolicyDocument, UUID(policy_document_id))
        if document is None:
            return
        chunks = self.policy_repository.list_chunks_for_document(document.id)
        for chunk in chunks:
            chunk.embedding_json = self.llm_provider.generate_embedding(chunk.content)
            chunk.token_count = chunk.token_count or len(chunk.content.split())
        document.embedding_status = "ready"
        self.db.commit()

    def retrieve_chunks(
        self,
        organization_id: UUID,
        store_id: UUID,
        query: str,
        *,
        document_type: str | None = None,
    ) -> list[dict[str, Any]]:
        chunks = retrieve_relevant_chunks(
            self.policy_repository,
            self.llm_provider,
            organization_id,
            store_id,
            query,
            document_type=document_type,
        )
        return [serialize_chunk(chunk) for chunk in chunks]

    def require_store_access(self, user_context: dict, store_id: UUID) -> UUID:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="forbidden", message="Organization context is required", status_code=403)
        organization_id = UUID(organization["id"])
        store = self.store_repository.get_store(organization_id, store_id)
        if store is None:
            raise AppError(code="not_found", message="Store not found", status_code=404)
        return organization_id
