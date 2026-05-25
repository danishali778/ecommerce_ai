def serialize_organization(organization) -> dict:
    return {
        "id": str(organization.id),
        "name": organization.name,
        "slug": organization.slug,
        "status": organization.status,
    }

