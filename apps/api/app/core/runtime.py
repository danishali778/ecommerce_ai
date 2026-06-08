from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
import inspect
from typing import Any

from app.core.errors import AppError, TransientUpstreamError
from app.core.redaction import redact_text


class FailureClass(StrEnum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    REQUIRES_OPERATOR = "requires_operator"


@dataclass(frozen=True)
class FailureInfo:
    failure_class: str
    failure_code: str
    retryable: bool
    redacted_message: str


TRANSIENT_APP_CODES = {
    "upstream_timeout",
    "upstream_rate_limit",
    "upstream_error",
}

REQUIRES_OPERATOR_CODES = {
    "source_snapshot_changed",
    "invalid_credentials",
    "integration_disconnected",
    "requires_operator",
}

PERMANENT_APP_CODES = {
    "validation_error",
    "forbidden",
    "not_found",
    "invalid_workflow_action",
    "invalid_workflow_condition",
    "invalid_workflow_trigger",
    "approval_terminal_state",
}


def classify_exception(exc: Exception) -> FailureInfo:
    message = redact_text(str(exc))

    if isinstance(exc, TransientUpstreamError):
        return FailureInfo(
            failure_class=FailureClass.TRANSIENT.value,
            failure_code="upstream_timeout",
            retryable=True,
            redacted_message=message,
        )

    if isinstance(exc, AppError):
        if exc.code in TRANSIENT_APP_CODES:
            return FailureInfo(FailureClass.TRANSIENT.value, exc.code, True, message)
        if exc.code in REQUIRES_OPERATOR_CODES:
            return FailureInfo(FailureClass.REQUIRES_OPERATOR.value, exc.code, False, message)
        if exc.code in PERMANENT_APP_CODES:
            return FailureInfo(FailureClass.PERMANENT.value, exc.code, False, message)
        if exc.status_code in {401, 403, 409}:
            return FailureInfo(FailureClass.REQUIRES_OPERATOR.value, exc.code, False, message)
        if exc.status_code >= 500:
            return FailureInfo(FailureClass.TRANSIENT.value, exc.code, True, message)
        return FailureInfo(FailureClass.PERMANENT.value, exc.code, False, message)

    lowered = message.lower()
    if any(token in lowered for token in ("timeout", "temporarily unavailable", "rate limit", "connection reset")):
        return FailureInfo(FailureClass.TRANSIENT.value, "upstream_timeout", True, message)
    if any(token in lowered for token in ("invalid credentials", "auth", "authorization", "disconnected")):
        return FailureInfo(FailureClass.REQUIRES_OPERATOR.value, "invalid_credentials", False, message)
    if any(token in lowered for token in ("schema", "validation", "malformed", "unsupported")):
        return FailureInfo(FailureClass.PERMANENT.value, "validation_failure", False, message)
    return FailureInfo(FailureClass.PERMANENT.value, exc.__class__.__name__.lower(), False, message)


def calculate_next_retry_at(*, retry_count: int, base_delay_seconds: int) -> datetime:
    delay_seconds = max(base_delay_seconds, 1) * (2**max(retry_count, 0))
    return datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)


def call_with_optional_trace(func, *args, trace_id: str | None = None, **kwargs):
    if trace_id is None:
        return func(*args, **kwargs)
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        signature = None
    if signature and "trace_id" in signature.parameters:
        return func(*args, trace_id=trace_id, **kwargs)
    return func(*args, **kwargs)


def runtime_metadata_dict(subject: Any) -> dict[str, Any]:
    fields = (
        "trace_id",
        "failure_class",
        "failure_code",
        "last_error_at",
        "next_retry_at",
        "max_retries",
        "attempt_count",
        "retry_count",
        "terminal_failed_at",
    )
    return {field: getattr(subject, field, None) for field in fields if hasattr(subject, field)}
