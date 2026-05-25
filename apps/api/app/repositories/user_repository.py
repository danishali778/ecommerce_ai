from uuid import UUID

from sqlalchemy import func, select

from app.repositories.base import Repository
from app.repositories.models import Role, User, UserRole


class UserRepository(Repository):
    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.scalar(select(User).where(User.id == user_id))

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(func.lower(User.email) == email.lower()))

    def list_by_organization(self, organization_id: UUID) -> list[User]:
        return list(self.db.scalars(select(User).where(User.organization_id == organization_id).order_by(User.created_at.desc())))

    def create(self, **values) -> User:
        user = User(**values)
        self.db.add(user)
        self.db.flush()
        return user

    def update(self, user: User, **values) -> User:
        for key, value in values.items():
            setattr(user, key, value)
        self.db.flush()
        return user

    def list_roles(self) -> list[Role]:
        return list(self.db.scalars(select(Role).order_by(Role.name.asc())))

    def get_roles_by_names(self, names: list[str]) -> list[Role]:
        if not names:
            return []
        return list(self.db.scalars(select(Role).where(Role.name.in_(names))))

    def get_role_by_name(self, name: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.name == name))

    def replace_user_roles(self, user_id: UUID, role_ids: list[UUID], assigned_by_user_id: UUID | None) -> None:
        self.db.query(UserRole).filter(UserRole.user_id == user_id).delete()
        for role_id in role_ids:
            self.db.add(UserRole(user_id=user_id, role_id=role_id, assigned_by_user_id=assigned_by_user_id))
        self.db.flush()

    def list_role_names_for_user(self, user_id: UUID) -> list[str]:
        rows = self.db.execute(
            select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        )
        return [row[0] for row in rows]

    def list_users_with_any_role(self, organization_id: UUID, role_names: list[str], active_only: bool = True) -> list[User]:
        query = (
            select(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(User.organization_id == organization_id, Role.name.in_(role_names))
            .distinct()
            .order_by(User.created_at.desc())
        )
        if active_only:
            query = query.where(User.status.in_(("active", "invited")))
        return list(self.db.scalars(query))
