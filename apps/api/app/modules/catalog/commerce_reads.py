from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission


def list_orders(module, user_context: dict, store_id: UUID) -> list[dict]:
    require_permission(user_context, Permission.SYNC_READ)
    store = module.require_store(user_context, store_id)
    orders = module.sync_repository.list_orders(store.organization_id, store.id)
    return [
        {
            "id": str(order.id),
            "external_order_id": order.external_order_id,
            "status": order.status,
            "payment_status": order.payment_status,
            "fulfillment_status": order.fulfillment_status,
            "total": str(order.total),
            "currency": order.currency,
            "created_at": order.created_at.isoformat(),
        }
        for order in orders
    ]


def get_order(module, user_context: dict, store_id: UUID, order_id: UUID) -> dict:
    require_permission(user_context, Permission.SYNC_READ)
    store = module.require_store(user_context, store_id)
    order = module.sync_repository.get_order(store.organization_id, store.id, order_id)
    if order is None:
        raise AppError(code="not_found", message="Order not found", status_code=404)
    return {
        "id": str(order.id),
        "external_order_id": order.external_order_id,
        "status": order.status,
        "payment_status": order.payment_status,
        "fulfillment_status": order.fulfillment_status,
        "total": str(order.total),
        "currency": order.currency,
        "created_at": order.created_at.isoformat(),
    }


def list_customers(module, user_context: dict, store_id: UUID) -> list[dict]:
    require_permission(user_context, Permission.SYNC_READ)
    store = module.require_store(user_context, store_id)
    customers = module.sync_repository.list_customers(store.organization_id, store.id)
    return [
        {
            "id": str(customer.id),
            "email": customer.email,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "total_orders": customer.total_orders,
            "created_at": customer.created_at.isoformat(),
        }
        for customer in customers
    ]


def get_customer(module, user_context: dict, store_id: UUID, customer_id: UUID) -> dict:
    require_permission(user_context, Permission.SYNC_READ)
    store = module.require_store(user_context, store_id)
    customer = module.sync_repository.get_customer(store.organization_id, store.id, customer_id)
    if customer is None:
        raise AppError(code="not_found", message="Customer not found", status_code=404)
    return {
        "id": str(customer.id),
        "email": customer.email,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "total_orders": customer.total_orders,
        "created_at": customer.created_at.isoformat(),
    }

