from fastapi import FastAPI

from app.api.routes import api_router
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
    )
    register_middleware(app, settings)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app
