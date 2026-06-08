from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import SuccessEnvelope
from app.api.schemas.notifications_ext import (
    NotificationChannelCreateRequest,
    NotificationChannelResponse,
    NotificationChannelTestResponse,
    NotificationDeliveryResponse,
    NotificationChannelUpdateRequest,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
)
from app.core.runtime import call_with_optional_trace
from app.core.responses import success_response
from app.services.notifications import NotificationService


router = APIRouter()


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


@router.get(
    "/{store_id}/notification-channels",
    response_model=SuccessEnvelope[list[NotificationChannelResponse]],
    summary="List notification channels",
)
def list_notification_channels(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    channels = service.list_channels(user_context, store_id)
    return success_response(request, channels, meta={"count": len(channels)})


@router.post(
    "/{store_id}/notification-channels",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[NotificationChannelResponse],
    summary="Create notification channel",
)
def create_notification_channel(
    store_id: UUID,
    payload: NotificationChannelCreateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    return success_response(request, service.create_channel(user_context, store_id, payload))


@router.get(
    "/{store_id}/notification-channels/{channel_id}",
    response_model=SuccessEnvelope[NotificationChannelResponse],
    summary="Get notification channel",
)
def get_notification_channel(
    store_id: UUID,
    channel_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    return success_response(request, service.get_channel(user_context, store_id, channel_id))


@router.patch(
    "/{store_id}/notification-channels/{channel_id}",
    response_model=SuccessEnvelope[NotificationChannelResponse],
    summary="Update notification channel",
)
def update_notification_channel(
    store_id: UUID,
    channel_id: UUID,
    payload: NotificationChannelUpdateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    return success_response(request, service.update_channel(user_context, store_id, channel_id, payload))


@router.delete(
    "/{store_id}/notification-channels/{channel_id}",
    response_model=SuccessEnvelope[dict],
    summary="Delete notification channel",
)
def delete_notification_channel(
    store_id: UUID,
    channel_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    return success_response(request, service.delete_channel(user_context, store_id, channel_id))


@router.post(
    "/{store_id}/notification-channels/{channel_id}/test",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessEnvelope[NotificationChannelTestResponse],
    summary="Queue notification channel test",
)
def test_notification_channel(
    store_id: UUID,
    channel_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    return success_response(
        request,
        call_with_optional_trace(
            service.test_channel,
            user_context,
            store_id,
            channel_id,
            trace_id=request.state.request_id,
        ),
    )


@router.get(
    "/{store_id}/notification-deliveries",
    response_model=SuccessEnvelope[list[NotificationDeliveryResponse]],
    summary="List notification deliveries",
)
def list_notification_deliveries(
    store_id: UUID,
    request: Request,
    status_filter: str | None = Query(default=None, alias="status"),
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    deliveries = service.list_deliveries(user_context, store_id, status=status_filter)
    return success_response(request, deliveries, meta={"count": len(deliveries)})


@router.get(
    "/{store_id}/notification-deliveries/{delivery_id}",
    response_model=SuccessEnvelope[NotificationDeliveryResponse],
    summary="Get notification delivery",
)
def get_notification_delivery(
    store_id: UUID,
    delivery_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    return success_response(request, service.get_delivery(user_context, store_id, delivery_id))


@router.post(
    "/{store_id}/notification-deliveries/{delivery_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessEnvelope[NotificationDeliveryResponse],
    summary="Retry failed notification delivery",
)
def retry_notification_delivery(
    store_id: UUID,
    delivery_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    return success_response(
        request,
        call_with_optional_trace(
            service.retry_delivery,
            user_context,
            store_id,
            delivery_id,
            trace_id=request.state.request_id,
        ),
    )


@router.get(
    "/{store_id}/notification-preferences",
    response_model=SuccessEnvelope[list[NotificationPreferenceResponse]],
    summary="List notification preferences",
)
def list_notification_preferences(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    preferences = service.list_preferences(user_context, store_id)
    return success_response(request, preferences, meta={"count": len(preferences)})


@router.patch(
    "/{store_id}/notification-preferences/{preference_id}",
    response_model=SuccessEnvelope[NotificationPreferenceResponse],
    summary="Update notification preference",
)
def update_notification_preference(
    store_id: UUID,
    preference_id: UUID,
    payload: NotificationPreferenceUpdateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: NotificationService = Depends(get_notification_service),
):
    return success_response(request, service.update_preference(user_context, store_id, preference_id, payload))
