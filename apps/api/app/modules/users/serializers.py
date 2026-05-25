def serialize_user(module, user) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "status": user.status,
        "roles": module.repository.list_role_names_for_user(user.id),
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }

