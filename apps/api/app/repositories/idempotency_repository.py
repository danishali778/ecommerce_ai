from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import IdempotencyRecord


class IdempotencyRepository(Repository):
    def get_record(self, organization_id: UUID, scope: str, idempotency_key: str) -> IdempotencyRecord | None:
        return self.db.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.organization_id == organization_id,
                IdempotencyRecord.scope == scope,
                IdempotencyRecord.idempotency_key == idempotency_key,
            )
        )

    def create_record(self, **values) -> IdempotencyRecord:
        record = IdempotencyRecord(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def update_record(self, record: IdempotencyRecord, **values) -> IdempotencyRecord:
        for key, value in values.items():
            setattr(record, key, value)
        self.db.flush()
        return record
