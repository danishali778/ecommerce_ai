from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import (
    CustomerSummary,
    OrderSummary,
    ProductDetail,
    ProductDraftSummary,
    ProductSummary,
    SuccessEnvelope,
    SyncRunSummary,
)
from app.api.schemas.stores import (
    DashboardSummaryResponse,
    DraftApprovalSubmissionResponse,
    DraftGenerateRequest,
    DraftGenerationAcceptedResponse,
    DraftUpdateRequest,
    InstallURLRequest,
    InstallURLResponse,
    StoreCreateRequest,
    StoreResponse,
    SubmitApprovalRequest,
    SyncRunCreateRequest,
)
from app.core.responses import success_response
from app.services.catalog import CatalogService
from app.services.dashboard import DashboardService
from app.services.stores import StoreService
from app.services.sync import SyncService


router = APIRouter()


def get_store_service(db: Session = Depends(get_db)) -> StoreService:
    return StoreService(db)


def get_sync_service(db: Session = Depends(get_db)) -> SyncService:
    return SyncService(db)


def get_catalog_service(db: Session = Depends(get_db)) -> CatalogService:
    return CatalogService(db)


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessEnvelope[StoreResponse], summary="Create store")
def create_store(
    payload: StoreCreateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: StoreService = Depends(get_store_service),
):
    store = service.create_store(user_context, payload)
    return success_response(request, store)


@router.get("", response_model=SuccessEnvelope[list[StoreResponse]], summary="List stores")
def list_stores(
    request: Request,
    user_context=Depends(get_current_user_context),
    service: StoreService = Depends(get_store_service),
):
    stores = service.list_stores(user_context)
    return success_response(request, stores, meta={"count": len(stores)})


@router.get("/{store_id}", response_model=SuccessEnvelope[StoreResponse], summary="Get store")
def get_store(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: StoreService = Depends(get_store_service),
):
    return success_response(request, service.get_store(user_context, store_id))


@router.post(
    "/{store_id}/shopify/install-url",
    response_model=SuccessEnvelope[InstallURLResponse],
    summary="Generate Shopify install URL",
)
def install_url(
    store_id: UUID,
    payload: InstallURLRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: StoreService = Depends(get_store_service),
):
    return success_response(request, service.generate_install_url(user_context, store_id, payload.redirect_uri))


@router.get("/{store_id}/integration", summary="Get store integration")
def get_integration(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: StoreService = Depends(get_store_service),
):
    return success_response(request, service.get_integration(user_context, store_id))


@router.post(
    "/{store_id}/sync-runs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessEnvelope[SyncRunSummary],
    summary="Queue store sync",
)
def create_sync_run(
    store_id: UUID,
    payload: SyncRunCreateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: SyncService = Depends(get_sync_service),
):
    return success_response(request, service.create_sync_run(user_context, store_id, payload.mode, idempotency_key))


@router.get("/{store_id}/sync-runs", response_model=SuccessEnvelope[list[SyncRunSummary]], summary="List sync runs")
def list_sync_runs(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: SyncService = Depends(get_sync_service),
):
    sync_runs = service.list_sync_runs(user_context, store_id)
    return success_response(request, sync_runs, meta={"count": len(sync_runs)})


@router.get("/{store_id}/sync-runs/{sync_run_id}", response_model=SuccessEnvelope[SyncRunSummary], summary="Get sync run")
def get_sync_run(
    store_id: UUID,
    sync_run_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: SyncService = Depends(get_sync_service),
):
    return success_response(request, service.get_sync_run(user_context, store_id, sync_run_id))


@router.post(
    "/{store_id}/sync-runs/{sync_run_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessEnvelope[SyncRunSummary],
    summary="Retry failed sync run",
)
def retry_sync_run(
    store_id: UUID,
    sync_run_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: SyncService = Depends(get_sync_service),
):
    return success_response(request, service.retry_sync_run(user_context, store_id, sync_run_id, idempotency_key))


@router.get(
    "/{store_id}/dashboard/summary",
    response_model=SuccessEnvelope[DashboardSummaryResponse],
    summary="Get dashboard summary",
)
def dashboard_summary(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: DashboardService = Depends(get_dashboard_service),
):
    return success_response(request, service.get_summary(user_context, store_id))


@router.get("/{store_id}/products", response_model=SuccessEnvelope[list[ProductSummary]], summary="List products")
def list_products(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: CatalogService = Depends(get_catalog_service),
):
    products = service.list_products(user_context, store_id)
    return success_response(request, products, meta={"count": len(products)})


@router.get("/{store_id}/products/{product_id}", response_model=SuccessEnvelope[ProductDetail], summary="Get product")
def get_product(
    store_id: UUID,
    product_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: CatalogService = Depends(get_catalog_service),
):
    return success_response(request, service.get_product(user_context, store_id, product_id))


@router.get(
    "/{store_id}/products/{product_id}/content-drafts",
    response_model=SuccessEnvelope[list[ProductDraftSummary]],
    summary="List product drafts",
)
def list_product_drafts(
    store_id: UUID,
    product_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: CatalogService = Depends(get_catalog_service),
):
    drafts = service.list_drafts(user_context, store_id, product_id)
    return success_response(request, drafts, meta={"count": len(drafts)})


@router.post(
    "/{store_id}/products/{product_id}/content-drafts/generate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessEnvelope[DraftGenerationAcceptedResponse],
    summary="Queue product draft generation",
)
def generate_product_draft(
    store_id: UUID,
    product_id: UUID,
    payload: DraftGenerateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: CatalogService = Depends(get_catalog_service),
):
    return success_response(request, service.generate_draft(user_context, store_id, product_id, payload))


@router.get(
    "/{store_id}/products/{product_id}/content-drafts/{draft_id}",
    response_model=SuccessEnvelope[ProductDraftSummary],
    summary="Get product draft",
)
def get_product_draft(
    store_id: UUID,
    product_id: UUID,
    draft_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: CatalogService = Depends(get_catalog_service),
):
    return success_response(request, service.get_draft(user_context, store_id, product_id, draft_id))


@router.patch(
    "/{store_id}/products/{product_id}/content-drafts/{draft_id}",
    response_model=SuccessEnvelope[ProductDraftSummary],
    summary="Update product draft",
)
def update_product_draft(
    store_id: UUID,
    product_id: UUID,
    draft_id: UUID,
    payload: DraftUpdateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: CatalogService = Depends(get_catalog_service),
):
    return success_response(request, service.update_draft(user_context, store_id, product_id, draft_id, payload))


@router.post(
    "/{store_id}/products/{product_id}/content-drafts/{draft_id}/submit-approval",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[DraftApprovalSubmissionResponse],
    summary="Submit draft for approval",
)
def submit_draft_approval(
    store_id: UUID,
    product_id: UUID,
    draft_id: UUID,
    payload: SubmitApprovalRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: CatalogService = Depends(get_catalog_service),
):
    return success_response(request, service.submit_draft_for_approval(user_context, store_id, product_id, draft_id, payload.reason, idempotency_key))


@router.get("/{store_id}/orders", response_model=SuccessEnvelope[list[OrderSummary]], summary="List orders")
def list_orders(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: CatalogService = Depends(get_catalog_service),
):
    orders = service.list_orders(user_context, store_id)
    return success_response(request, orders, meta={"count": len(orders)})


@router.get("/{store_id}/orders/{order_id}", response_model=SuccessEnvelope[OrderSummary], summary="Get order")
def get_order(
    store_id: UUID,
    order_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: CatalogService = Depends(get_catalog_service),
):
    return success_response(request, service.get_order(user_context, store_id, order_id))


@router.get("/{store_id}/customers", response_model=SuccessEnvelope[list[CustomerSummary]], summary="List customers")
def list_customers(
    store_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: CatalogService = Depends(get_catalog_service),
):
    customers = service.list_customers(user_context, store_id)
    return success_response(request, customers, meta={"count": len(customers)})


@router.get("/{store_id}/customers/{customer_id}", response_model=SuccessEnvelope[CustomerSummary], summary="Get customer")
def get_customer(
    store_id: UUID,
    customer_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: CatalogService = Depends(get_catalog_service),
):
    return success_response(request, service.get_customer(user_context, store_id, customer_id))
