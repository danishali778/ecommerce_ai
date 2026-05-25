from app.integrations.supabase_auth import SupabaseAuthClient
from app.modules.auth import AuthModule


class AuthService:
    def __init__(self, db, auth_client: SupabaseAuthClient | None = None, module: AuthModule | None = None) -> None:
        self.db = db
        self.auth_client = auth_client or SupabaseAuthClient()
        self.module = module or AuthModule(db=db, auth_client=self.auth_client)

    def register(self, payload) -> dict:
        return self.module.register(payload)

    def login(self, payload) -> dict:
        return self.module.login(payload)

    def refresh(self, refresh_token: str | None) -> dict:
        return self.module.refresh(refresh_token)

    def logout(self, refresh_token: str | None) -> None:
        self.module.logout(refresh_token)

    def get_current_user_context(self, access_token: str) -> dict:
        return self.module.get_current_user_context(access_token)
