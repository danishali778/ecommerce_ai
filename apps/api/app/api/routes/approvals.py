from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.approvals import ApprovalActionResponse, ApprovalDecisionRequest, ApprovalResponse
from app.api.schemas.common import SuccessEnvelope
from app.core.responses import success_response
from app.services.approvals import ApprovalService


router = APIRouter()


def get_approval_service(db: Session = Depends(get_db)) -> ApprovalService:
    return ApprovalService(db)


@router.get("", response_model=SuccessEnvelope[list[ApprovalResponse]], summary="List approvals")
def list_approvals(
    request: Request,
    user_context=Depends(get_current_user_context),
    service: ApprovalService = Depends(get_approval_service),
):
    approvals = service.list_approvals(user_context)
    return success_response(request, approvals, meta={"count": len(approvals)})


@router.get("/{approval_id}", response_model=SuccessEnvelope[ApprovalResponse], summary="Get approval")
def get_approval(
    approval_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: ApprovalService = Depends(get_approval_service),
):
    return success_response(request, service.get_approval(user_context, approval_id))


@router.post("/{approval_id}/approve", response_model=SuccessEnvelope[ApprovalActionResponse], summary="Approve and queue execution")
def approve(
    approval_id: UUID,
    payload: ApprovalDecisionRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: ApprovalService = Depends(get_approval_service),
):
    return success_response(request, service.approve(user_context, approval_id, payload.review_notes, idempotency_key))


@router.post("/{approval_id}/reject", response_model=SuccessEnvelope[ApprovalActionResponse], summary="Reject approval")
def reject(
    approval_id: UUID,
    payload: ApprovalDecisionRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: ApprovalService = Depends(get_approval_service),
):
    return success_response(request, service.reject(user_context, approval_id, payload.review_notes, idempotency_key))


@router.post("/{approval_id}/cancel", response_model=SuccessEnvelope[ApprovalActionResponse], summary="Cancel approval")
def cancel(
    approval_id: UUID,
    payload: ApprovalDecisionRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: ApprovalService = Depends(get_approval_service),
):
    return success_response(request, service.cancel(user_context, approval_id, payload.review_notes, idempotency_key))


@router.post(
    "/{approval_id}/retry-execution",
    response_model=SuccessEnvelope[ApprovalActionResponse],
    summary="Retry failed approval execution",
)
def retry_execution(
    approval_id: UUID,
    payload: ApprovalDecisionRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: ApprovalService = Depends(get_approval_service),
):
    return success_response(request, service.retry_execution(user_context, approval_id, payload.review_notes, idempotency_key))
