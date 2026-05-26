from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import SuccessEnvelope
from app.api.schemas.inventory import InventoryAlertResponse, ReorderSuggestionResponse, SupplierReorderDraftUpsertRequest
from app.core.responses import success_response
from app.services.inventory import InventoryService


router = APIRouter()


def get_inventory_service(db: Session = Depends(get_db)) -> InventoryService:
    return InventoryService(db)


@router.get(
    "/{store_id}/inventory/alerts",
    response_model=SuccessEnvelope[list[InventoryAlertResponse]],
    summary="List inventory alerts",
)
def list_inventory_alerts(
    store_id: UUID,
    request: Request,
    status_filter: str | None = Query(default=None, alias="status"),
    user_context=Depends(get_current_user_context),
    service: InventoryService = Depends(get_inventory_service),
):
    alerts = service.list_alerts(user_context, store_id, status=status_filter)
    return success_response(request, alerts, meta={"count": len(alerts)})


@router.get(
    "/{store_id}/inventory/reorder-suggestions",
    response_model=SuccessEnvelope[list[ReorderSuggestionResponse]],
    summary="List reorder suggestions",
)
def list_reorder_suggestions(
    store_id: UUID,
    request: Request,
    status_filter: str | None = Query(default=None, alias="status"),
    user_context=Depends(get_current_user_context),
    service: InventoryService = Depends(get_inventory_service),
):
    suggestions = service.list_reorder_suggestions(user_context, store_id, status=status_filter)
    return success_response(request, suggestions, meta={"count": len(suggestions)})


@router.get(
    "/{store_id}/inventory/reorder-suggestions/{suggestion_id}",
    response_model=SuccessEnvelope[ReorderSuggestionResponse],
    summary="Get reorder suggestion",
)
def get_reorder_suggestion(
    store_id: UUID,
    suggestion_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: InventoryService = Depends(get_inventory_service),
):
    return success_response(request, service.get_reorder_suggestion(user_context, store_id, suggestion_id))


@router.post(
    "/{store_id}/inventory/reorder-suggestions/{suggestion_id}/supplier-drafts",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[ReorderSuggestionResponse],
    summary="Create or refresh supplier reorder draft",
)
def create_or_refresh_supplier_draft(
    store_id: UUID,
    suggestion_id: UUID,
    payload: SupplierReorderDraftUpsertRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: InventoryService = Depends(get_inventory_service),
):
    return success_response(request, service.create_or_refresh_supplier_draft(user_context, store_id, suggestion_id, payload))
