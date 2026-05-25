from app.core.errors import AppError


def register(module, payload) -> dict:
    auth_result = module.auth_client.sign_up(payload.email, payload.password, {"full_name": payload.full_name})
    user = auth_result.get("user") or {}
    app_user = module.user_repository.get_by_email(payload.email)
    if app_user is None and user.get("id"):
        app_user = module.user_repository.create(
            id=user["id"],
            organization_id=None,
            email=payload.email,
            full_name=payload.full_name,
            status="active",
        )
        module.db.commit()
    return {
        "access_token": auth_result.get("access_token"),
        "refresh_token": auth_result.get("refresh_token"),
        "token_type": auth_result.get("token_type", "bearer"),
        "expires_in": auth_result.get("expires_in", 3600),
        "user": {
            "id": user.get("id"),
            "email": user.get("email", payload.email),
            "full_name": payload.full_name,
            "app_user_id": str(app_user.id) if app_user else None,
        },
        "organization": None,
        "available_roles": [],
    }


def ensure_user_is_active(status: str) -> None:
    if status in {"suspended", "disabled"}:
        raise AppError(code="forbidden", message="User account is not active", status_code=403)

