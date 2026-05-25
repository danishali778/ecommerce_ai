def serialize_notification(notification) -> dict:
    return {
        "id": str(notification.id),
        "type": notification.type,
        "channel": notification.channel,
        "title": notification.title,
        "body": notification.body,
        "status": notification.status,
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
        "created_at": notification.created_at.isoformat(),
        "store_id": str(notification.store_id) if notification.store_id else None,
    }

