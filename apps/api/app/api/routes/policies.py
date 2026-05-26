from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import SuccessEnvelope
from app.api.schemas.policies import PolicyDocumentCreateRequest, PolicyDocumentResponse, PolicyDocumentUpdateRequest
from app.core.responses import success_response
from app.services.policies import PoliciesService


router = APIRouter()


def get_policy_service(db: Session = Depends(get_db)) -> PoliciesService:
    return PoliciesService(db)


@router.post(
    "/{store_id}/policies",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[PolicyDocumentResponse],
    summary="Create policy document",
)
def create_policy_document(
    store_id: UUID,
    payload: PolicyDocumentCreateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: PoliciesService = Depends(get_policy_service),
):
    return success_response(request, service.create_document(user_context, store_id, payload))


@router.get(
    "/{store_id}/policies",
    response_model=SuccessEnvelope[list[PolicyDocumentResponse]],
    summary="List policy documents",
)
def list_policy_documents(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: PoliciesService = Depends(get_policy_service),
):
    documents = service.list_documents(user_context, store_id)
    return success_response(request, documents, meta={"count": len(documents)})


@router.get(
    "/{store_id}/policies/{policy_id}",
    response_model=SuccessEnvelope[PolicyDocumentResponse],
    summary="Get policy document",
)
def get_policy_document(
    store_id: UUID,
    policy_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: PoliciesService = Depends(get_policy_service),
):
    return success_response(request, service.get_document(user_context, store_id, policy_id))


@router.patch(
    "/{store_id}/policies/{policy_id}",
    response_model=SuccessEnvelope[PolicyDocumentResponse],
    summary="Update policy document",
)
def update_policy_document(
    store_id: UUID,
    policy_id: UUID,
    payload: PolicyDocumentUpdateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: PoliciesService = Depends(get_policy_service),
):
    return success_response(request, service.update_document(user_context, store_id, policy_id, payload))
