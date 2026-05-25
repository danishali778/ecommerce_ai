from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_auth_service, get_current_user_context
from app.api.schemas.auth import AuthTokenResponse, LoginRequest, MeResponse, RegisterRequest
from app.api.schemas.common import SuccessEnvelope
from app.core.responses import success_response
from app.core.settings import get_settings
from app.services.auth import AuthService


router = APIRouter()


def _set_refresh_cookie(response: Response, refresh_token: str | None) -> None:
    if not refresh_token:
        return
    settings = get_settings()
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=SuccessEnvelope[AuthTokenResponse], summary="Register user")
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = auth_service.register(payload)
    _set_refresh_cookie(response, result.pop("refresh_token", None))
    return success_response(request, result)


@router.post("/login", response_model=SuccessEnvelope[AuthTokenResponse], summary="Login user")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = auth_service.login(payload)
    _set_refresh_cookie(response, result.pop("refresh_token", None))
    return success_response(request, result)


@router.post("/refresh", response_model=SuccessEnvelope[AuthTokenResponse], summary="Refresh session")
def refresh(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    settings = get_settings()
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    result = auth_service.refresh(refresh_token)
    _set_refresh_cookie(response, result.pop("refresh_token", None))
    return success_response(request, result)


@router.post("/logout", response_model=SuccessEnvelope[dict], summary="Logout user")
def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    settings = get_settings()
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    auth_service.logout(refresh_token)
    response.delete_cookie(settings.refresh_cookie_name, path="/")
    return success_response(request, {"logged_out": True})


@router.get("/me", response_model=SuccessEnvelope[MeResponse], summary="Get current session context")
def me(request: Request, user_context=Depends(get_current_user_context)):
    return success_response(request, user_context)
