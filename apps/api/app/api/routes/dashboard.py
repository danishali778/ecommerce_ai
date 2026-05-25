from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import AgentRunSummary, AuditEventSummary, SuccessEnvelope, WorkflowRunSummary
from app.core.responses import success_response
from app.services.dashboard import DashboardService


router = APIRouter()


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


@router.get("/{store_id}/workflow-runs", response_model=SuccessEnvelope[list[WorkflowRunSummary]], summary="List workflow runs")
def list_workflow_runs(
    store_id: UUID,
    request: Request,
    status: str | None = Query(default=None),
    workflow_key: str | None = Query(default=None),
    trigger_type: str | None = Query(default=None),
    user_context=Depends(get_current_user_context),
    service: DashboardService = Depends(get_dashboard_service),
):
    data = service.list_workflow_runs(
        user_context,
        store_id,
        status=status,
        workflow_key=workflow_key,
        trigger_type=trigger_type,
    )
    return success_response(request, data, meta={"count": len(data)})


@router.get(
    "/{store_id}/workflow-runs/{workflow_run_id}",
    response_model=SuccessEnvelope[WorkflowRunSummary],
    summary="Get workflow run",
)
def get_workflow_run(
    store_id: UUID,
    workflow_run_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: DashboardService = Depends(get_dashboard_service),
):
    return success_response(request, service.get_workflow_run(user_context, store_id, workflow_run_id))


@router.get("/{store_id}/agent-runs", response_model=SuccessEnvelope[list[AgentRunSummary]], summary="List agent runs")
def list_agent_runs(
    store_id: UUID,
    request: Request,
    agent_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    workflow_run_id: UUID | None = Query(default=None),
    user_context=Depends(get_current_user_context),
    service: DashboardService = Depends(get_dashboard_service),
):
    data = service.list_agent_runs(
        user_context,
        store_id,
        agent_type=agent_type,
        status=status,
        workflow_run_id=workflow_run_id,
    )
    return success_response(request, data, meta={"count": len(data)})


@router.get(
    "/{store_id}/agent-runs/{agent_run_id}",
    response_model=SuccessEnvelope[AgentRunSummary],
    summary="Get agent run",
)
def get_agent_run(
    store_id: UUID,
    agent_run_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: DashboardService = Depends(get_dashboard_service),
):
    return success_response(request, service.get_agent_run(user_context, store_id, agent_run_id))


@router.get("/{store_id}/audit-events", response_model=SuccessEnvelope[list[AuditEventSummary]], summary="List audit events")
def list_audit_events(
    store_id: UUID,
    request: Request,
    entity_type: str | None = Query(default=None),
    action_type: str | None = Query(default=None),
    user_id: UUID | None = Query(default=None),
    user_context=Depends(get_current_user_context),
    service: DashboardService = Depends(get_dashboard_service),
):
    data = service.list_audit_events(
        user_context,
        store_id,
        entity_type=entity_type,
        action_type=action_type,
        user_id=user_id,
    )
    return success_response(request, data, meta={"count": len(data)})
