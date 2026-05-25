from app.modules.catalog import CatalogModule


class CatalogService:
    def __init__(self, db, module: CatalogModule | None = None) -> None:
        self.db = db
        self.module = module or CatalogModule(db)

    def list_products(self, user_context: dict, store_id) -> list[dict]:
        return self.module.list_products(user_context, store_id)

    def get_product(self, user_context: dict, store_id, product_id) -> dict:
        return self.module.get_product(user_context, store_id, product_id)

    def list_drafts(self, user_context: dict, store_id, product_id) -> list[dict]:
        return self.module.list_drafts(user_context, store_id, product_id)

    def generate_draft(self, user_context: dict, store_id, product_id, payload) -> dict:
        result = self.module.generate_draft(user_context, store_id, product_id, payload)
        if result.pop("_enqueue_generation", False):
            self._enqueue_generation(result["agent_run_id"])
        return result

    def get_draft(self, user_context: dict, store_id, product_id, draft_id) -> dict:
        return self.module.get_draft(user_context, store_id, product_id, draft_id)

    def update_draft(self, user_context: dict, store_id, product_id, draft_id, payload) -> dict:
        return self.module.update_draft(user_context, store_id, product_id, draft_id, payload)

    def submit_draft_for_approval(
        self,
        user_context: dict,
        store_id,
        product_id,
        draft_id,
        reason: str,
        idempotency_key: str | None,
    ) -> dict:
        return self.module.submit_draft_for_approval(user_context, store_id, product_id, draft_id, reason, idempotency_key)

    def list_orders(self, user_context: dict, store_id) -> list[dict]:
        return self.module.list_orders(user_context, store_id)

    def get_order(self, user_context: dict, store_id, order_id) -> dict:
        return self.module.get_order(user_context, store_id, order_id)

    def list_customers(self, user_context: dict, store_id) -> list[dict]:
        return self.module.list_customers(user_context, store_id)

    def get_customer(self, user_context: dict, store_id, customer_id) -> dict:
        return self.module.get_customer(user_context, store_id, customer_id)

    @staticmethod
    def _enqueue_generation(agent_run_id: str) -> None:
        from app.tasks.catalog import generate_product_content_draft

        generate_product_content_draft.delay(agent_run_id)
