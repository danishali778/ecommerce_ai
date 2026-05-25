from __future__ import annotations

import hashlib
import json
from uuid import UUID

from app.core.errors import AppError
from app.repositories.idempotency_repository import IdempotencyRepository


def build_request_fingerprint(payload: dict | None) -> str:
    canonical = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def resolve_idempotent_response(
    repository: IdempotencyRepository,
    *,
    organization_id: UUID,
    scope: str,
    idempotency_key: str | None,
    payload: dict | None = None,
) -> tuple[dict | None, object | None, str]:
    if not idempotency_key:
        raise AppError(code="validation_error", message="Idempotency-Key header is required", status_code=422)
    fingerprint = build_request_fingerprint(payload)
    record = repository.get_record(organization_id, scope, idempotency_key)
    if record is None:
        return None, None, fingerprint
    if record.request_fingerprint and record.request_fingerprint != fingerprint:
        raise AppError(code="idempotency_conflict", message="Idempotency key already used with a different payload", status_code=409)
    return record.response_json, record, fingerprint
