from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.redaction import redact_value


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = HTTPStatus.BAD_REQUEST,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = redact_value(details or {})


class TransientUpstreamError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def error_response(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": redact_value(exc.message),
                "details": redact_value(exc.details),
            },
            "meta": {
                "request_id": getattr(request.state, "request_id", None),
            },
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return error_response(request, exc)
