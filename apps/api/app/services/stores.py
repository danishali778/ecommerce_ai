from app.modules.stores import StoreModule


class StoreService:
    def __init__(self, db, module: StoreModule | None = None) -> None:
        self.db = db
        self.module = module or StoreModule(db)

    def create_store(self, user_context: dict, payload) -> dict:
        return self.module.create_store(user_context, payload)

    def list_stores(self, user_context: dict) -> list[dict]:
        return self.module.list_stores(user_context)

    def get_store(self, user_context: dict, store_id) -> dict:
        return self.module.get_store(user_context, store_id)

    def generate_install_url(self, user_context: dict, store_id, redirect_uri: str) -> dict:
        return self.module.generate_install_url(user_context, store_id, redirect_uri)

    def handle_callback(self, shop: str, code: str, state: str, hmac_value: str, query_params: dict[str, str]) -> dict:
        return self.module.handle_callback(shop, code, state, hmac_value, query_params)

    def get_integration(self, user_context: dict, store_id) -> dict:
        return self.module.get_integration(user_context, store_id)
