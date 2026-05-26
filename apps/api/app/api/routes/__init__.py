from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.approvals import router as approvals_router
from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.fraud import router as fraud_router
from app.api.routes.health import router as health_router
from app.api.routes.integrations import router as integrations_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.organizations import router as organizations_router
from app.api.routes.policies import router as policies_router
from app.api.routes.shopify_callback import router as shopify_callback_router
from app.api.routes.stores import router as stores_router
from app.api.routes.support import router as support_router
from app.api.routes.users import router as users_router


api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(shopify_callback_router, tags=["integrations"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(integrations_router, prefix="/integrations", tags=["integrations"])
api_router.include_router(stores_router, prefix="/stores", tags=["stores"])
api_router.include_router(approvals_router, prefix="/approvals", tags=["approvals"])
api_router.include_router(dashboard_router, prefix="/stores", tags=["dashboard"])
api_router.include_router(policies_router, prefix="/stores", tags=["policies"])
api_router.include_router(support_router, prefix="/stores", tags=["support"])
api_router.include_router(fraud_router, prefix="/stores", tags=["fraud"])
api_router.include_router(inventory_router, prefix="/stores", tags=["inventory"])
api_router.include_router(analytics_router, prefix="/stores", tags=["analytics"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
