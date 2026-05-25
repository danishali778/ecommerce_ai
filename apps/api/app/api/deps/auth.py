from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps.db import get_db
from app.core.errors import AppError
from app.integrations.supabase_auth import SupabaseAuthClient
from app.services.auth import AuthService


bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db=db, auth_client=SupabaseAuthClient())


def get_current_user_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    if credentials is None:
        raise AppError(code="unauthenticated", message="Authentication required", status_code=401)
    return auth_service.get_current_user_context(credentials.credentials)
