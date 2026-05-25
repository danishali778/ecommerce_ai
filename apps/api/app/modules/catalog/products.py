from uuid import UUID

from app.core.authz import require_permission
from app.core.errors import AppError
from app.core.permissions import Permission

from .serializers import serialize_draft, serialize_product, serialize_variant


def list_products(module, user_context: dict, store_id: UUID) -> list[dict]:
    require_permission(user_context, Permission.CATALOG_READ)
    store = module.require_store(user_context, store_id)
    products = module.sync_repository.list_products(store.organization_id, store.id)
    return [
        serialize_product(
            product,
            variants=module.sync_repository.list_variants(store.organization_id, store.id, product.id),
        )
        for product in products
    ]


def get_product(module, user_context: dict, store_id: UUID, product_id: UUID) -> dict:
    require_permission(user_context, Permission.CATALOG_READ)
    store = module.require_store(user_context, store_id)
    product = module.sync_repository.get_product(store.organization_id, store.id, product_id)
    if product is None:
        raise AppError(code="not_found", message="Product not found", status_code=404)
    drafts = module.catalog_repository.list_drafts(store.organization_id, store.id, product.id)
    variants = module.sync_repository.list_variants(store.organization_id, store.id, product.id)
    payload = serialize_product(product, variants=variants)
    payload["variants"] = [serialize_variant(variant) for variant in variants]
    payload["latest_draft"] = serialize_draft(drafts[0]) if drafts else None
    return payload

