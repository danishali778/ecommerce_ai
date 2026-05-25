from uuid import UUID

from app.core.errors import AppError
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository

from .serializers import serialize_organization


class OrganizationModule:
    def __init__(self, db) -> None:
        self.db = db
        self.organization_repository = OrganizationRepository(db)
        self.user_repository = UserRepository(db)

    def create_initial_organization(self, user_context: dict, payload) -> dict:
        if user_context.get("organization"):
            raise AppError(code="conflict", message="Organization already exists for this deployment", status_code=409)
        user_id = UUID(user_context["user"]["id"])
        app_user = self.user_repository.get_by_id(user_id)
        if app_user is None:
            raise AppError(code="not_found", message="Application user must exist before organization bootstrap", status_code=404)
        if self.organization_repository.get_by_slug(payload.slug):
            raise AppError(code="conflict", message="Organization slug already exists", status_code=409)
        organization = self.organization_repository.create(name=payload.name, slug=payload.slug, status="active")
        self.user_repository.update(app_user, organization_id=organization.id)
        self.db.flush()
        organization.owner_user_id = app_user.id
        owner_roles = self.user_repository.get_roles_by_names(["Owner"])
        self.user_repository.replace_user_roles(app_user.id, [role.id for role in owner_roles], app_user.id)
        self.db.commit()
        return serialize_organization(organization)

    def get_current_organization(self, user_context: dict) -> dict:
        organization = user_context.get("organization")
        if organization is None:
            raise AppError(code="not_found", message="No active organization", status_code=404)
        organization_record = self.organization_repository.get_by_id(UUID(organization["id"]))
        if organization_record is None:
            raise AppError(code="not_found", message="Organization not found", status_code=404)
        return serialize_organization(organization_record)
