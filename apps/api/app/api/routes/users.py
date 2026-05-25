from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import SuccessEnvelope
from app.api.schemas.users import CreateUserRequest, UpdateUserRequest
from app.api.schemas.users import RoleResponse, UserResponse
from app.core.responses import success_response
from app.services.users import UserService


router = APIRouter()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/users", response_model=SuccessEnvelope[list[UserResponse]], summary="List users")
def list_users(
    request: Request,
    status_filter: str | None = Query(default=None, alias="status"),
    role: str | None = None,
    q: str | None = None,
    user_context=Depends(get_current_user_context),
    service: UserService = Depends(get_user_service),
):
    users = service.list_users(user_context, status_filter=status_filter, role=role, query=q)
    return success_response(request, users, meta={"count": len(users)})


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=SuccessEnvelope[UserResponse], summary="Create user")
def create_user(
    payload: CreateUserRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: UserService = Depends(get_user_service),
):
    user = service.create_internal_user(user_context, payload)
    return success_response(request, user)


@router.patch("/users/{user_id}", response_model=SuccessEnvelope[UserResponse], summary="Update user")
def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: UserService = Depends(get_user_service),
):
    user = service.update_internal_user(user_context, user_id, payload)
    return success_response(request, user)


@router.get("/roles", response_model=SuccessEnvelope[list[RoleResponse]], summary="List built-in roles")
def list_roles(
    request: Request,
    user_context=Depends(get_current_user_context),
    service: UserService = Depends(get_user_service),
):
    roles = service.list_roles(user_context)
    return success_response(request, roles, meta={"count": len(roles)})
