from __future__ import annotations

from collections.abc import Iterable


class Permission:
    ORG_MANAGE = "org.manage"
    USERS_MANAGE = "users.manage"
    STORES_MANAGE = "stores.manage"
    INTEGRATIONS_MANAGE = "integrations.manage"
    SYNC_READ = "sync.read"
    SYNC_TRIGGER = "sync.trigger"
    CATALOG_READ = "catalog.read"
    CATALOG_DRAFT_GENERATE = "catalog.draft_generate"
    CATALOG_DRAFT_EDIT = "catalog.draft_edit"
    CATALOG_DRAFT_SUBMIT = "catalog.draft_submit"
    APPROVALS_READ = "approvals.read"
    APPROVALS_REVIEW = "approvals.review"
    APPROVALS_CANCEL = "approvals.cancel"
    APPROVALS_RETRY_EXECUTION = "approvals.retry_execution"
    LOGS_READ = "logs.read"
    NOTIFICATIONS_READ = "notifications.read"
    NOTIFICATIONS_UPDATE = "notifications.update"


ALL_PERMISSIONS = [
    Permission.ORG_MANAGE,
    Permission.USERS_MANAGE,
    Permission.STORES_MANAGE,
    Permission.INTEGRATIONS_MANAGE,
    Permission.SYNC_READ,
    Permission.SYNC_TRIGGER,
    Permission.CATALOG_READ,
    Permission.CATALOG_DRAFT_GENERATE,
    Permission.CATALOG_DRAFT_EDIT,
    Permission.CATALOG_DRAFT_SUBMIT,
    Permission.APPROVALS_READ,
    Permission.APPROVALS_REVIEW,
    Permission.APPROVALS_CANCEL,
    Permission.APPROVALS_RETRY_EXECUTION,
    Permission.LOGS_READ,
    Permission.NOTIFICATIONS_READ,
    Permission.NOTIFICATIONS_UPDATE,
]


ROLE_PERMISSION_MAP: dict[str, list[str]] = {
    "Owner": ALL_PERMISSIONS,
    "Admin": ALL_PERMISSIONS,
    "Manager": [
        Permission.SYNC_READ,
        Permission.SYNC_TRIGGER,
        Permission.CATALOG_READ,
        Permission.CATALOG_DRAFT_GENERATE,
        Permission.CATALOG_DRAFT_EDIT,
        Permission.CATALOG_DRAFT_SUBMIT,
        Permission.APPROVALS_READ,
        Permission.APPROVALS_REVIEW,
        Permission.APPROVALS_CANCEL,
        Permission.APPROVALS_RETRY_EXECUTION,
        Permission.LOGS_READ,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_UPDATE,
    ],
    "Marketing User": [
        Permission.CATALOG_READ,
        Permission.CATALOG_DRAFT_GENERATE,
        Permission.CATALOG_DRAFT_EDIT,
        Permission.CATALOG_DRAFT_SUBMIT,
        Permission.APPROVALS_READ,
        Permission.LOGS_READ,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_UPDATE,
    ],
    "Support Agent": [
        Permission.CATALOG_READ,
        Permission.SYNC_READ,
        Permission.LOGS_READ,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_UPDATE,
    ],
    "Viewer": [
        Permission.CATALOG_READ,
        Permission.SYNC_READ,
        Permission.LOGS_READ,
        Permission.NOTIFICATIONS_READ,
    ],
}


def resolve_permissions(role_names: Iterable[str]) -> list[str]:
    permissions: set[str] = set()
    for role_name in role_names:
        permissions.update(ROLE_PERMISSION_MAP.get(role_name, []))
    return sorted(permissions)
