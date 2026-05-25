from __future__ import annotations

import re
from typing import Any


SENSITIVE_KEYWORDS = (
    "token",
    "secret",
    "password",
    "authorization",
    "access_key",
    "refresh_key",
    "client_secret",
    "api_key",
)

TOKEN_PATTERN = re.compile(r"(?i)\b(?:shpat|shpss|sk|pk|rk)_[A-Za-z0-9_\-]{8,}\b")


def redact_text(value: str) -> str:
    return TOKEN_PATTERN.sub("[REDACTED]", value)


def redact_value(value: Any, *, key: str | None = None) -> Any:
    if key and any(keyword in key.lower() for keyword in SENSITIVE_KEYWORDS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {item_key: redact_value(item_value, key=item_key) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if isinstance(value, str):
        return redact_text(value)
    return value
