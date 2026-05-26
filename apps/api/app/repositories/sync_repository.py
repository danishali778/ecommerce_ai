from uuid import UUID

from sqlalchemy import and_, select

from app.repositories.base import Repository
from app.repositories.models import (
    Customer,
    Order,
    OrderItem,
    Product,
    ProductVariant,
    SyncRun,
)


class SyncRepository(Repository):
    def create_sync_run(self, **values) -> SyncRun:
        sync_run = SyncRun(**values)
        self.db.add(sync_run)
        self.db.flush()
        return sync_run

    def get_sync_run(self, organization_id: UUID, store_id: UUID, sync_run_id: UUID) -> SyncRun | None:
        return self.db.scalar(
            select(SyncRun).where(
                SyncRun.organization_id == organization_id,
                SyncRun.store_id == store_id,
                SyncRun.id == sync_run_id,
            )
        )

    def list_sync_runs(self, organization_id: UUID, store_id: UUID) -> list[SyncRun]:
        return list(
            self.db.scalars(
                select(SyncRun)
                .where(SyncRun.organization_id == organization_id, SyncRun.store_id == store_id)
                .order_by(SyncRun.created_at.desc())
            )
        )

    def get_active_sync_run(self, store_id: UUID) -> SyncRun | None:
        return self.db.scalar(
            select(SyncRun).where(
                SyncRun.store_id == store_id,
                SyncRun.status.in_(("queued", "running")),
            )
        )

    def upsert_product(self, organization_id: UUID, store_id: UUID, payload: dict) -> Product:
        existing = self.db.scalar(
            select(Product).where(Product.store_id == store_id, Product.external_product_id == str(payload["external_product_id"]))
        )
        values = {
            "organization_id": organization_id,
            "store_id": store_id,
            "external_product_id": str(payload["external_product_id"]),
            "handle": payload["handle"],
            "title": payload["title"],
            "description": payload.get("description"),
            "vendor": payload.get("vendor"),
            "category": payload.get("category"),
            "tags": payload.get("tags", []),
            "seo_title": payload.get("seo_title"),
            "seo_description": payload.get("seo_description"),
            "status": payload.get("status", "active"),
            "is_archived": False,
            "archived_at": None,
            "last_sync_run_id": payload.get("last_sync_run_id"),
            "last_synced_at": payload.get("last_synced_at"),
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
            self.db.flush()
            return existing
        product = Product(**values)
        self.db.add(product)
        self.db.flush()
        return product

    def archive_missing_products(self, organization_id: UUID, store_id: UUID, external_product_ids: set[str], archived_at) -> None:
        products = list(
            self.db.scalars(
                select(Product).where(Product.organization_id == organization_id, Product.store_id == store_id)
            )
        )
        for product in products:
            if product.external_product_id not in external_product_ids:
                product.is_archived = True
                product.archived_at = archived_at
            else:
                product.is_archived = False
                product.archived_at = None
        self.db.flush()

    def upsert_variant(self, organization_id: UUID, store_id: UUID, product_id: UUID, payload: dict) -> ProductVariant:
        existing = self.db.scalar(
            select(ProductVariant).where(
                ProductVariant.store_id == store_id,
                ProductVariant.external_variant_id == str(payload["external_variant_id"]),
            )
        )
        values = {
            "organization_id": organization_id,
            "store_id": store_id,
            "product_id": product_id,
            "external_variant_id": str(payload["external_variant_id"]),
            "sku": payload.get("sku"),
            "title": payload.get("title", ""),
            "price": payload.get("price", 0),
            "cost": payload.get("cost"),
            "inventory_quantity": payload.get("inventory_quantity", 0),
            "compare_at_price": payload.get("compare_at_price"),
            "last_sync_run_id": payload.get("last_sync_run_id"),
            "last_synced_at": payload.get("last_synced_at"),
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
            self.db.flush()
            return existing
        variant = ProductVariant(**values)
        self.db.add(variant)
        self.db.flush()
        return variant

    def upsert_customer(self, organization_id: UUID, store_id: UUID, payload: dict) -> Customer:
        existing = self.db.scalar(
            select(Customer).where(Customer.store_id == store_id, Customer.external_customer_id == str(payload["external_customer_id"]))
        )
        values = {
            "organization_id": organization_id,
            "store_id": store_id,
            "external_customer_id": str(payload["external_customer_id"]),
            "email": payload.get("email"),
            "first_name": payload.get("first_name"),
            "last_name": payload.get("last_name"),
            "phone": payload.get("phone"),
            "total_orders": payload.get("total_orders", 0),
            "total_spend": payload.get("total_spend", 0),
            "total_refunds": payload.get("total_refunds", 0),
            "last_sync_run_id": payload.get("last_sync_run_id"),
            "last_synced_at": payload.get("last_synced_at"),
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
            self.db.flush()
            return existing
        customer = Customer(**values)
        self.db.add(customer)
        self.db.flush()
        return customer

    def upsert_order(self, organization_id: UUID, store_id: UUID, payload: dict) -> Order:
        existing = self.db.scalar(
            select(Order).where(Order.store_id == store_id, Order.external_order_id == str(payload["external_order_id"]))
        )
        values = {
            "organization_id": organization_id,
            "store_id": store_id,
            "external_order_id": str(payload["external_order_id"]),
            "customer_id": payload.get("customer_id"),
            "status": payload.get("status", "open"),
            "payment_status": payload.get("payment_status"),
            "fulfillment_status": payload.get("fulfillment_status"),
            "billing_country": payload.get("billing_country"),
            "shipping_country": payload.get("shipping_country"),
            "billing_postal_code": payload.get("billing_postal_code"),
            "shipping_postal_code": payload.get("shipping_postal_code"),
            "payment_attempt_count": payload.get("payment_attempt_count", 0),
            "subtotal": payload.get("subtotal", 0),
            "total": payload.get("total", 0),
            "currency": payload.get("currency"),
            "last_sync_run_id": payload.get("last_sync_run_id"),
            "last_synced_at": payload.get("last_synced_at"),
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
            self.db.flush()
            return existing
        order = Order(**values)
        self.db.add(order)
        self.db.flush()
        return order

    def replace_order_items(self, organization_id: UUID, store_id: UUID, order_id: UUID, items: list[dict]) -> None:
        self.db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
        for item in items:
            self.db.add(
                OrderItem(
                    organization_id=organization_id,
                    store_id=store_id,
                    order_id=order_id,
                    product_id=item.get("product_id"),
                    variant_id=item.get("variant_id"),
                    external_line_item_id=item.get("external_line_item_id"),
                    sku=item.get("sku"),
                    title=item["title"],
                    quantity=item["quantity"],
                    unit_price=item.get("unit_price", 0),
                    total_price=item.get("total_price", 0),
                )
            )
        self.db.flush()

    def list_products(self, organization_id: UUID, store_id: UUID) -> list[Product]:
        return list(
            self.db.scalars(
                select(Product)
                .where(Product.organization_id == organization_id, Product.store_id == store_id)
                .order_by(Product.updated_at.desc())
            )
        )

    def get_product(self, organization_id: UUID, store_id: UUID, product_id: UUID) -> Product | None:
        return self.db.scalar(
            select(Product).where(Product.organization_id == organization_id, Product.store_id == store_id, Product.id == product_id)
        )

    def list_variants(self, organization_id: UUID, store_id: UUID, product_id: UUID) -> list[ProductVariant]:
        return list(
            self.db.scalars(
                select(ProductVariant)
                .where(
                    ProductVariant.organization_id == organization_id,
                    ProductVariant.store_id == store_id,
                    ProductVariant.product_id == product_id,
                )
                .order_by(ProductVariant.created_at.asc())
            )
        )

    def get_variant(self, organization_id: UUID, store_id: UUID, variant_id: UUID) -> ProductVariant | None:
        return self.db.scalar(
            select(ProductVariant).where(
                ProductVariant.organization_id == organization_id,
                ProductVariant.store_id == store_id,
                ProductVariant.id == variant_id,
            )
        )

    def list_variants_for_store(self, organization_id: UUID, store_id: UUID) -> list[ProductVariant]:
        return list(
            self.db.scalars(
                select(ProductVariant)
                .where(ProductVariant.organization_id == organization_id, ProductVariant.store_id == store_id)
                .order_by(ProductVariant.updated_at.desc())
            )
        )

    def list_orders(self, organization_id: UUID, store_id: UUID) -> list[Order]:
        return list(
            self.db.scalars(
                select(Order)
                .where(Order.organization_id == organization_id, Order.store_id == store_id)
                .order_by(Order.created_at.desc())
            )
        )

    def get_order(self, organization_id: UUID, store_id: UUID, order_id: UUID) -> Order | None:
        return self.db.scalar(
            select(Order).where(Order.organization_id == organization_id, Order.store_id == store_id, Order.id == order_id)
        )

    def list_customers(self, organization_id: UUID, store_id: UUID) -> list[Customer]:
        return list(
            self.db.scalars(
                select(Customer)
                .where(Customer.organization_id == organization_id, Customer.store_id == store_id)
                .order_by(Customer.created_at.desc())
            )
        )

    def get_customer(self, organization_id: UUID, store_id: UUID, customer_id: UUID) -> Customer | None:
        return self.db.scalar(
            select(Customer).where(
                Customer.organization_id == organization_id,
                Customer.store_id == store_id,
                Customer.id == customer_id,
            )
        )

    def list_orders_for_sync_run(self, sync_run_id: UUID) -> list[Order]:
        return list(
            self.db.scalars(
                select(Order)
                .where(Order.last_sync_run_id == sync_run_id)
                .order_by(Order.updated_at.desc())
            )
        )

    def list_variants_for_sync_run(self, sync_run_id: UUID) -> list[ProductVariant]:
        return list(
            self.db.scalars(
                select(ProductVariant)
                .where(ProductVariant.last_sync_run_id == sync_run_id)
                .order_by(ProductVariant.updated_at.desc())
            )
        )
