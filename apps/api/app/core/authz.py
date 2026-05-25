from __future__ import annotations

from app.core.errors import AppError


def require_permission(user_context: dict, permission: str) -> None:
    permissions = set(user_context.get("permissions", []))
    if permission not in permissions:
        raise AppError(code="forbidden", message="Insufficient permissions", status_code=403)


def require_any_permission(user_context: dict, permissions: list[str]) -> None:
    resolved = set(user_context.get("permissions", []))
    if resolved.intersection(permissions):
        return
    raise AppError(code="forbidden", message="Insufficient permissions", status_code=403)
