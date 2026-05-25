from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import NotificationSummary, SuccessEnvelope
from app.core.responses import success_response
from app.services.notifications import NotificationService


router = APIRouter()


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


@router.get("", response_model=SuccessEnvelope[list[NotificationSummary]], summary="List notifications")
def list_notifications(
    request: Request,
    status: str | None = Query(default=None),
    type: str | None = Query(default=None),
    store_id: UUID | None = Query(default=None),
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    notifications = service.list_notifications(user_context, status=status, notification_type=type, store_id=store_id)
    return success_response(request, notifications, meta={"count": len(notifications)})


@router.patch("/{notification_id}/read", response_model=SuccessEnvelope[NotificationSummary], summary="Mark notification as read")
def mark_notification_read(
    notification_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    return success_response(request, service.mark_as_read(user_context, notification_id))
