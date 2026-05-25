from datetime import datetime, timezone
from typing import Any

from fastapi import Request


def success_response(request: Request, data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    payload_meta = {
        "request_id": getattr(request.state, "request_id", None),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if meta:
        payload_meta.update(meta)
    return {"data": data, "meta": payload_meta}
