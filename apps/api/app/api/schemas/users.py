from pydantic import BaseModel, EmailStr, Field

from app.api.schemas.common import RoleSummary, UserSummary


class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role_names: list[str]


class UpdateUserRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = None
    role_names: list[str] | None = None


class UserResponse(UserSummary):
    roles: list[str]


class RoleResponse(RoleSummary):
    pass
