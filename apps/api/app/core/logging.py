import logging
from logging.config import dictConfig

from app.core.redaction import redact_text
from app.core.settings import Settings


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg)
        if record.args:
            record.args = tuple(redact_text(arg) if isinstance(arg, str) else arg for arg in record.args)
        return True


def configure_logging(settings: Settings) -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "redact": {
                    "()": RedactingFilter,
                }
            },
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["redact"],
                }
            },
            "root": {
                "handlers": ["default"],
                "level": settings.log_level.upper(),
            },
        }
    )
    logging.getLogger(__name__).debug("Logging configured")
