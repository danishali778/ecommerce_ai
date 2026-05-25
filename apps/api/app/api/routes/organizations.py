from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import SuccessEnvelope
from app.api.schemas.organizations import OrganizationCreateRequest
from app.api.schemas.organizations import OrganizationResponse
from app.core.responses import success_response
from app.services.organizations import OrganizationService


router = APIRouter()


def get_org_service(db: Session = Depends(get_db)) -> OrganizationService:
    return OrganizationService(db)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessEnvelope[OrganizationResponse], summary="Create initial organization")
def create_organization(
    payload: OrganizationCreateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: OrganizationService = Depends(get_org_service),
):
    organization = service.create_initial_organization(user_context, payload)
    return success_response(request, organization)


@router.get("/current", response_model=SuccessEnvelope[OrganizationResponse], summary="Get current organization")
def get_current_organization(
    request: Request,
    user_context=Depends(get_current_user_context),
    service: OrganizationService = Depends(get_org_service),
):
    organization = service.get_current_organization(user_context)
    return success_response(request, organization)
