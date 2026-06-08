from uuid import UUID

from fastapi import APIRouter, Body, Depends, Header, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import SuccessEnvelope
from app.api.schemas.pricing import (
    PriceRecommendationResponse,
    PricingRuleCreateRequest,
    PricingRuleResponse,
    PricingRuleUpdateRequest,
    PricingSimulationRequest,
    PricingSimulationResponse,
    ReferencePriceCreateRequest,
    ReferencePriceImportResponse,
)
from app.core.responses import success_response
from app.services.pricing import PricingService


router = APIRouter()


def get_pricing_service(db: Session = Depends(get_db)) -> PricingService:
    return PricingService(db)


@router.get("/{store_id}/pricing/rules", response_model=SuccessEnvelope[list[PricingRuleResponse]], summary="List pricing rules")
def list_pricing_rules(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: PricingService = Depends(get_pricing_service),
):
    rules = service.list_rules(user_context, store_id)
    return success_response(request, rules, meta={"count": len(rules)})


@router.post("/{store_id}/pricing/rules", status_code=status.HTTP_201_CREATED, response_model=SuccessEnvelope[PricingRuleResponse], summary="Create pricing rule")
def create_pricing_rule(
    store_id: UUID,
    payload: PricingRuleCreateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: PricingService = Depends(get_pricing_service),
):
    return success_response(request, service.create_rule(user_context, store_id, payload))


@router.get("/{store_id}/pricing/rules/{rule_id}", response_model=SuccessEnvelope[PricingRuleResponse], summary="Get pricing rule")
def get_pricing_rule(
    store_id: UUID,
    rule_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: PricingService = Depends(get_pricing_service),
):
    return success_response(request, service.get_rule(user_context, store_id, rule_id))


@router.patch("/{store_id}/pricing/rules/{rule_id}", response_model=SuccessEnvelope[PricingRuleResponse], summary="Update pricing rule")
def update_pricing_rule(
    store_id: UUID,
    rule_id: UUID,
    payload: PricingRuleUpdateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: PricingService = Depends(get_pricing_service),
):
    return success_response(request, service.update_rule(user_context, store_id, rule_id, payload))


@router.delete("/{store_id}/pricing/rules/{rule_id}", response_model=SuccessEnvelope[dict], summary="Delete pricing rule")
def delete_pricing_rule(
    store_id: UUID,
    rule_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: PricingService = Depends(get_pricing_service),
):
    return success_response(request, service.delete_rule(user_context, store_id, rule_id))


@router.post("/{store_id}/pricing/reference-prices", status_code=status.HTTP_201_CREATED, response_model=SuccessEnvelope[dict], summary="Create manual reference price input")
def create_reference_price(
    store_id: UUID,
    payload: ReferencePriceCreateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: PricingService = Depends(get_pricing_service),
):
    _ = idempotency_key
    return success_response(request, service.create_reference_price(user_context, store_id, payload))


@router.post(
    "/{store_id}/pricing/reference-prices/import",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessEnvelope[ReferencePriceImportResponse],
    summary="Import pricing reference prices from CSV",
)
def import_reference_prices(
    store_id: UUID,
    request: Request,
    csv_bytes: bytes = Body(..., media_type="text/csv"),
    user_context=Depends(get_current_user_context),
    service: PricingService = Depends(get_pricing_service),
):
    return success_response(request, service.import_reference_prices(user_context, store_id, csv_bytes))


@router.post("/{store_id}/pricing/simulate", response_model=SuccessEnvelope[PricingSimulationResponse], summary="Simulate pricing strategy")
def simulate_price(
    store_id: UUID,
    payload: PricingSimulationRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: PricingService = Depends(get_pricing_service),
):
    return success_response(request, service.simulate(user_context, store_id, payload))


@router.get("/{store_id}/pricing/recommendations", response_model=SuccessEnvelope[list[PriceRecommendationResponse]], summary="List price recommendations")
def list_price_recommendations(
    store_id: UUID,
    request: Request,
    status: str | None = Query(default=None),
    user_context=Depends(get_current_user_context),
    service: PricingService = Depends(get_pricing_service),
):
    recommendations = service.list_recommendations(user_context, store_id, status=status)
    return success_response(request, recommendations, meta={"count": len(recommendations)})


@router.get(
    "/{store_id}/pricing/recommendations/{recommendation_id}",
    response_model=SuccessEnvelope[PriceRecommendationResponse],
    summary="Get price recommendation",
)
def get_price_recommendation(
    store_id: UUID,
    recommendation_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: PricingService = Depends(get_pricing_service),
):
    return success_response(request, service.get_recommendation(user_context, store_id, recommendation_id))
