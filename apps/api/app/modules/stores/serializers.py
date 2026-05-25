def serialize_store(store) -> dict:
    return {
        "id": str(store.id),
        "name": store.name,
        "platform": store.platform,
        "domain": store.domain,
        "currency": store.currency,
        "timezone": store.timezone,
        "connection_status": store.connection_status,
        "last_successful_sync_at": store.last_successful_sync_at.isoformat() if store.last_successful_sync_at else None,
        "created_at": store.created_at.isoformat(),
        "updated_at": store.updated_at.isoformat(),
    }

