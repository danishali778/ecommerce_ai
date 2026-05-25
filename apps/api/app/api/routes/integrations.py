from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps.db import get_db
from app.api.schemas.common import SuccessEnvelope
from app.core.responses import success_response
from app.services.stores import StoreService


router = APIRouter()


def get_store_service(db: Session = Depends(get_db)) -> StoreService:
    return StoreService(db)


@router.get("/shopify/callback", response_model=SuccessEnvelope[dict], summary="Handle Shopify OAuth callback")
def shopify_callback(
    request: Request,
    shop: str = Query(...),
    code: str = Query(...),
    state: str = Query(...),
    hmac: str = Query(...),
    service: StoreService = Depends(get_store_service),
):
    return success_response(request, service.handle_callback(shop, code, state, hmac, dict(request.query_params)))
