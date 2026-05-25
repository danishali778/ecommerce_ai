from uuid import UUID

from sqlalchemy import func, select

from app.core.authz import require_permission
from app.core.permissions import Permission
from app.repositories.models import ApprovalRequest, AgentRun, Customer, Order, Product, SyncRun, WorkflowRun


def get_summary(module, user_context: dict, store_id: UUID) -> dict:
    require_permission(user_context, Permission.SYNC_READ)
    store = module.require_store(user_context, store_id)
    latest_sync = module.db.scalar(
        select(SyncRun).where(SyncRun.store_id == store.id).order_by(SyncRun.created_at.desc()).limit(1)
    )
    recent_workflow_failures = module.db.scalar(
        select(func.count()).select_from(WorkflowRun).where(WorkflowRun.store_id == store.id, WorkflowRun.status == "failed")
    )
    pending_approvals = module.db.scalar(
        select(func.count()).select_from(ApprovalRequest).where(ApprovalRequest.store_id == store.id, ApprovalRequest.status == "pending")
    )
    recent_agent_runs = module.db.scalar(select(func.count()).select_from(AgentRun).where(AgentRun.store_id == store.id))
    product_count = module.db.scalar(select(func.count()).select_from(Product).where(Product.store_id == store.id))
    order_count = module.db.scalar(select(func.count()).select_from(Order).where(Order.store_id == store.id))
    customer_count = module.db.scalar(select(func.count()).select_from(Customer).where(Customer.store_id == store.id))
    return {
        "latest_sync_status": latest_sync.status if latest_sync else None,
        "latest_sync_completed_at": latest_sync.completed_at.isoformat() if latest_sync and latest_sync.completed_at else None,
        "product_count": product_count or 0,
        "order_count": order_count or 0,
        "customer_count": customer_count or 0,
        "low_inventory_count": module.count_low_inventory(store.id),
        "pending_approval_count": pending_approvals or 0,
        "recent_workflow_failures": recent_workflow_failures or 0,
        "recent_agent_runs": recent_agent_runs or 0,
    }

