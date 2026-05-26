from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import SuccessEnvelope
from app.api.schemas.fraud import OrderRiskScoreResponse, RiskReviewDecisionRequest, RiskReviewResponse
from app.core.responses import success_response
from app.services.fraud import FraudService


router = APIRouter()


def get_fraud_service(db: Session = Depends(get_db)) -> FraudService:
    return FraudService(db)


@router.get(
    "/{store_id}/orders/{order_id}/risk-score",
    response_model=SuccessEnvelope[OrderRiskScoreResponse],
    summary="Get order risk score",
)
def get_order_risk_score(
    store_id: UUID,
    order_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: FraudService = Depends(get_fraud_service),
):
    return success_response(request, service.get_order_risk_score(user_context, store_id, order_id))


@router.get(
    "/{store_id}/risk-reviews",
    response_model=SuccessEnvelope[list[RiskReviewResponse]],
    summary="List risk reviews",
)
def list_risk_reviews(
    store_id: UUID,
    request: Request,
    risk_status: str | None = Query(default=None),
    user_context=Depends(get_current_user_context),
    service: FraudService = Depends(get_fraud_service),
):
    reviews = service.list_risk_reviews(user_context, store_id, risk_status=risk_status)
    return success_response(request, reviews, meta={"count": len(reviews)})


@router.get(
    "/{store_id}/risk-reviews/{risk_review_id}",
    response_model=SuccessEnvelope[RiskReviewResponse],
    summary="Get risk review",
)
def get_risk_review(
    store_id: UUID,
    risk_review_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: FraudService = Depends(get_fraud_service),
):
    return success_response(request, service.get_risk_review(user_context, store_id, risk_review_id))


@router.post(
    "/{store_id}/risk-reviews/{risk_review_id}/decision",
    response_model=SuccessEnvelope[RiskReviewResponse],
    summary="Record risk review decision",
)
def record_risk_review_decision(
    store_id: UUID,
    risk_review_id: UUID,
    payload: RiskReviewDecisionRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: FraudService = Depends(get_fraud_service),
):
    return success_response(request, service.record_decision(user_context, store_id, risk_review_id, payload))
