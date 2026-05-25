from .registration import ensure_user_is_active
from .serializers import serialize_organization


def login(module, payload) -> dict:
    auth_result = module.auth_client.sign_in(payload.email, payload.password)
    user_info = auth_result.get("user") or {}
    app_user = module.user_repository.get_by_email(payload.email)
    if app_user is None and user_info.get("id"):
        app_user = module.user_repository.create(
            id=user_info["id"],
            organization_id=None,
            email=payload.email,
            full_name=(user_info.get("user_metadata") or {}).get("full_name", ""),
            status="active",
        )
    roles = module.user_repository.list_role_names_for_user(app_user.id) if app_user else []
    organization = module.organization_repository.get_by_id(app_user.organization_id) if app_user and app_user.organization_id else None
    if app_user:
        ensure_user_is_active(app_user.status)
        module.user_repository.update(app_user, last_login_at=user_info.get("last_sign_in_at"))
        module.db.commit()
    return {
        "access_token": auth_result.get("access_token"),
        "refresh_token": auth_result.get("refresh_token"),
        "token_type": auth_result.get("token_type", "bearer"),
        "expires_in": auth_result.get("expires_in", 3600),
        "user": {
            "id": user_info.get("id"),
            "email": user_info.get("email", payload.email),
            "full_name": app_user.full_name if app_user else "",
            "status": app_user.status if app_user else "invited",
        },
        "organization": serialize_organization(organization) if organization else None,
        "available_roles": roles,
    }


def refresh(module, refresh_token: str | None) -> dict:
    if not refresh_token:
        from app.core.errors import AppError

        raise AppError(code="unauthenticated", message="Missing refresh token", status_code=401)
    result = module.auth_client.refresh(refresh_token)
    return {
        "access_token": result.get("access_token"),
        "refresh_token": result.get("refresh_token"),
        "token_type": result.get("token_type", "bearer"),
        "expires_in": result.get("expires_in", 3600),
    }


def logout(module, refresh_token: str | None) -> None:
    if not refresh_token:
        return
    refreshed = module.auth_client.refresh(refresh_token)
    access_token = refreshed.get("access_token")
    if access_token:
        module.auth_client.sign_out(access_token)

