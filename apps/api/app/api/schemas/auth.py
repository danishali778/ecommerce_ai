from pydantic import BaseModel, EmailStr, Field

from app.api.schemas.common import RoleSummary, StoreSummary


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthUserContext(BaseModel):
    id: str
    email: str
    full_name: str
    status: str


class AuthOrganizationContext(BaseModel):
    id: str
    name: str
    slug: str
    status: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict | None = None
    organization: dict | None = None
    available_roles: list[str] = Field(default_factory=list)


class MeResponse(BaseModel):
    user: AuthUserContext
    organization: AuthOrganizationContext | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    accessible_stores: list[StoreSummary] = Field(default_factory=list)
    available_role_summaries: list[RoleSummary] = Field(default_factory=list)
