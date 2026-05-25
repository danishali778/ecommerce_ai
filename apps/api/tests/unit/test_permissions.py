import pytest

from app.core.authz import require_any_permission, require_permission
from app.core.errors import AppError
from app.core.permissions import Permission, resolve_permissions


def test_resolve_permissions_merges_roles_without_duplicates():
    permissions = resolve_permissions(["Owner", "Viewer", "Viewer"])

    assert Permission.USERS_MANAGE in permissions
    assert Permission.CATALOG_READ in permissions
    assert len(permissions) == len(set(permissions))


def test_require_permission_rejects_missing_permission():
    user_context = {"permissions": [Permission.CATALOG_READ]}

    with pytest.raises(AppError) as exc:
        require_permission(user_context, Permission.APPROVALS_REVIEW)

    assert exc.value.status_code == 403


def test_require_any_permission_accepts_any_matching_permission():
    user_context = {"permissions": [Permission.NOTIFICATIONS_READ]}

    require_any_permission(user_context, [Permission.SYNC_READ, Permission.NOTIFICATIONS_READ])
