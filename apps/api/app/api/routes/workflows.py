from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import SuccessEnvelope
from app.api.schemas.workflows import (
    WorkflowCreateRequest,
    WorkflowResponse,
    WorkflowTestRequest,
    WorkflowTestResponse,
    WorkflowUpdateRequest,
)
from app.core.responses import success_response
from app.services.workflows import WorkflowService


router = APIRouter()


def get_workflow_service(db: Session = Depends(get_db)) -> WorkflowService:
    return WorkflowService(db)


@router.get("/{store_id}/workflows", response_model=SuccessEnvelope[list[WorkflowResponse]], summary="List workflows")
def list_workflows(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: WorkflowService = Depends(get_workflow_service),
):
    workflows = service.list_workflows(user_context, store_id)
    return success_response(request, workflows, meta={"count": len(workflows)})


@router.post("/{store_id}/workflows", status_code=status.HTTP_201_CREATED, response_model=SuccessEnvelope[WorkflowResponse], summary="Create workflow")
def create_workflow(
    store_id: UUID,
    payload: WorkflowCreateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: WorkflowService = Depends(get_workflow_service),
):
    return success_response(request, service.create_workflow(user_context, store_id, payload))


@router.get("/{store_id}/workflows/{workflow_id}", response_model=SuccessEnvelope[WorkflowResponse], summary="Get workflow")
def get_workflow(
    store_id: UUID,
    workflow_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: WorkflowService = Depends(get_workflow_service),
):
    return success_response(request, service.get_workflow(user_context, store_id, workflow_id))


@router.patch("/{store_id}/workflows/{workflow_id}", response_model=SuccessEnvelope[WorkflowResponse], summary="Update workflow")
def update_workflow(
    store_id: UUID,
    workflow_id: UUID,
    payload: WorkflowUpdateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: WorkflowService = Depends(get_workflow_service),
):
    return success_response(request, service.update_workflow(user_context, store_id, workflow_id, payload))


@router.delete("/{store_id}/workflows/{workflow_id}", response_model=SuccessEnvelope[dict], summary="Delete workflow")
def delete_workflow(
    store_id: UUID,
    workflow_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: WorkflowService = Depends(get_workflow_service),
):
    return success_response(request, service.delete_workflow(user_context, store_id, workflow_id))


@router.post("/{store_id}/workflows/{workflow_id}/enable", response_model=SuccessEnvelope[WorkflowResponse], summary="Enable workflow")
def enable_workflow(
    store_id: UUID,
    workflow_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: WorkflowService = Depends(get_workflow_service),
):
    return success_response(request, service.enable_workflow(user_context, store_id, workflow_id))


@router.post("/{store_id}/workflows/{workflow_id}/disable", response_model=SuccessEnvelope[WorkflowResponse], summary="Disable workflow")
def disable_workflow(
    store_id: UUID,
    workflow_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: WorkflowService = Depends(get_workflow_service),
):
    return success_response(request, service.disable_workflow(user_context, store_id, workflow_id))


@router.post("/{store_id}/workflows/{workflow_id}/test", response_model=SuccessEnvelope[WorkflowTestResponse], summary="Test workflow")
def test_workflow(
    store_id: UUID,
    workflow_id: UUID,
    payload: WorkflowTestRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: WorkflowService = Depends(get_workflow_service),
):
    return success_response(request, service.test_workflow(user_context, store_id, workflow_id, payload))
