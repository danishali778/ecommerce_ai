from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AuthTokens:
    access_token: str
    refresh_token: str | None
    token_type: str = "bearer"
    expires_in: int = 3600
