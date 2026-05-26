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
    SUPPORT_READ = "support.read"
    SUPPORT_WRITE = "support.write"
    SUPPORT_GENERATE = "support.generate"
    POLICIES_READ = "policies.read"
    POLICIES_MANAGE = "policies.manage"
    INVENTORY_READ = "inventory.read"
    INVENTORY_MANAGE = "inventory.manage"
    FRAUD_READ = "fraud.read"
    FRAUD_REVIEW = "fraud.review"
    ANALYTICS_READ = "analytics.read"


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
    Permission.SUPPORT_READ,
    Permission.SUPPORT_WRITE,
    Permission.SUPPORT_GENERATE,
    Permission.POLICIES_READ,
    Permission.POLICIES_MANAGE,
    Permission.INVENTORY_READ,
    Permission.INVENTORY_MANAGE,
    Permission.FRAUD_READ,
    Permission.FRAUD_REVIEW,
    Permission.ANALYTICS_READ,
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
        Permission.SUPPORT_READ,
        Permission.SUPPORT_WRITE,
        Permission.SUPPORT_GENERATE,
        Permission.POLICIES_READ,
        Permission.POLICIES_MANAGE,
        Permission.INVENTORY_READ,
        Permission.INVENTORY_MANAGE,
        Permission.FRAUD_READ,
        Permission.FRAUD_REVIEW,
        Permission.ANALYTICS_READ,
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
        Permission.POLICIES_READ,
        Permission.ANALYTICS_READ,
    ],
    "Support Agent": [
        Permission.CATALOG_READ,
        Permission.SYNC_READ,
        Permission.LOGS_READ,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_UPDATE,
        Permission.SUPPORT_READ,
        Permission.SUPPORT_WRITE,
        Permission.SUPPORT_GENERATE,
        Permission.POLICIES_READ,
        Permission.FRAUD_READ,
        Permission.ANALYTICS_READ,
    ],
    "Viewer": [
        Permission.CATALOG_READ,
        Permission.SYNC_READ,
        Permission.LOGS_READ,
        Permission.NOTIFICATIONS_READ,
        Permission.POLICIES_READ,
        Permission.INVENTORY_READ,
        Permission.FRAUD_READ,
        Permission.ANALYTICS_READ,
    ],
}


def resolve_permissions(role_names: Iterable[str]) -> list[str]:
    permissions: set[str] = set()
    for role_name in role_names:
        permissions.update(ROLE_PERMISSION_MAP.get(role_name, []))
    return sorted(permissions)
