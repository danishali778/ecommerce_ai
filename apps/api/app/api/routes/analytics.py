from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.analytics import AnalyticsAutomationResponse, AnalyticsOverviewResponse
from app.api.schemas.common import SuccessEnvelope
from app.core.responses import success_response
from app.services.analytics import AnalyticsService


router = APIRouter()


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get(
    "/{store_id}/analytics/overview",
    response_model=SuccessEnvelope[AnalyticsOverviewResponse],
    summary="Get analytics overview",
)
def get_analytics_overview(
    store_id: UUID,
    request: Request,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    user_context=Depends(get_current_user_context),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return success_response(request, service.get_overview(user_context, store_id, date_from=date_from, date_to=date_to))


@router.get(
    "/{store_id}/analytics/automation",
    response_model=SuccessEnvelope[AnalyticsAutomationResponse],
    summary="Get automation analytics",
)
def get_analytics_automation(
    store_id: UUID,
    request: Request,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    user_context=Depends(get_current_user_context),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return success_response(request, service.get_automation(user_context, store_id, date_from=date_from, date_to=date_to))
