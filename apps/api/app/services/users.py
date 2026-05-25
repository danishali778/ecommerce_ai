from app.modules.users import UserModule


class UserService:
    def __init__(self, db, module: UserModule | None = None) -> None:
        self.db = db
        self.module = module or UserModule(db)

    def list_users(self, user_context: dict, status_filter: str | None, role: str | None, query: str | None) -> list[dict]:
        return self.module.list_users(user_context, status_filter, role, query)

    def create_internal_user(self, user_context: dict, payload) -> dict:
        return self.module.create_internal_user(user_context, payload)

    def update_internal_user(self, user_context: dict, user_id: str, payload) -> dict:
        return self.module.update_internal_user(user_context, user_id, payload)

    def list_roles(self, user_context: dict) -> list[dict]:
        return self.module.list_roles(user_context)
