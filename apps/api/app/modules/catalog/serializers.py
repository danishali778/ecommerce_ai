def serialize_product(product, *, variants: list | None = None) -> dict:
    inventory_total = sum(variant.inventory_quantity for variant in variants or [])
    return {
        "id": str(product.id),
        "title": product.title,
        "handle": product.handle,
        "vendor": product.vendor,
        "status": product.status,
        "seo_title": product.seo_title,
        "inventory_total": inventory_total,
        "updated_at": product.updated_at.isoformat(),
    }


def serialize_variant(variant) -> dict:
    return {
        "id": str(variant.id),
        "external_variant_id": variant.external_variant_id,
        "sku": variant.sku,
        "title": variant.title,
        "price": str(variant.price),
        "compare_at_price": str(variant.compare_at_price) if variant.compare_at_price is not None else None,
        "inventory_quantity": variant.inventory_quantity,
    }


def serialize_draft(draft) -> dict:
    return {
        "id": str(draft.id),
        "product_id": str(draft.product_id),
        "generated_title": draft.generated_title,
        "generated_description": draft.generated_description,
        "generated_tags": draft.generated_tags,
        "generated_seo_title": draft.generated_seo_title,
        "generated_seo_description": draft.generated_seo_description,
        "model_name": draft.model_name,
        "status": draft.status,
        "created_at": draft.created_at.isoformat(),
        "updated_at": draft.updated_at.isoformat(),
    }

