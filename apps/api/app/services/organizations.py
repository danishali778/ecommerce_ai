from app.modules.organizations import OrganizationModule


class OrganizationService:
    def __init__(self, db, module: OrganizationModule | None = None) -> None:
        self.db = db
        self.module = module or OrganizationModule(db)

    def create_initial_organization(self, user_context: dict, payload) -> dict:
        return self.module.create_initial_organization(user_context, payload)

    def get_current_organization(self, user_context: dict) -> dict:
        return self.module.get_current_organization(user_context)
