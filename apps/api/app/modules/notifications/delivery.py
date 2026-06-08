from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from urllib.parse import urlparse
from uuid import UUID

import httpx

from app.core.redaction import redact_text
from app.core.secret_store import get_secret_store
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository


DEFAULT_EVENT_TYPES = [
    "sync_failed",
    "approval_pending",
    "workflow_failed",
    "pricing_approval_pending",
    "pricing_recommendation_blocked",
    "workflow_alert",
]


def queue_external_deliveries(db, notification, event_type: str, trace_id: str | None = None) -> list:
    repository = NotificationRepository(db)
    deliveries = []
    for channel in repository.list_enabled_channels_for_event(notification.organization_id, notification.store_id, event_type):
        delivery = repository.create_delivery(
            organization_id=notification.organization_id,
            store_id=notification.store_id,
            notification_id=notification.id,
            channel_id=channel.id,
            event_type=event_type,
            status="queued",
            trace_id=trace_id,
            rendered_payload_json={},
            response_payload_json={},
            last_error=None,
            attempt_count=0,
            queued_at=datetime.now(timezone.utc),
            last_attempted_at=None,
            sent_at=None,
            created_at=datetime.now(timezone.utc),
        )
        from app.tasks.notifications import send_external_notification_delivery

        send_external_notification_delivery.delay(str(delivery.id), trace_id)
        deliveries.append(delivery)
    return deliveries


def queue_channel_test_delivery(db, channel, requested_by_user_id: UUID, trace_id: str | None = None) -> object:
    repository = NotificationRepository(db)
    user_repository = UserRepository(db)
    user = user_repository.get_by_id(requested_by_user_id)
    notification = repository.update(
        repository.create_for_test_notification(
            organization_id=channel.organization_id,
            store_id=channel.store_id,
            user_id=requested_by_user_id,
            title=f"Test delivery for {channel.name}",
            body="CommerceOps AI notification channel test.",
            payload_json={"channel_id": str(channel.id)},
        ),
        status="unread",
    )
    delivery = repository.create_delivery(
        organization_id=channel.organization_id,
        store_id=channel.store_id,
        notification_id=notification.id,
        channel_id=channel.id,
        event_type="manual_test",
        status="queued",
        trace_id=trace_id,
        rendered_payload_json={"title": notification.title, "body": notification.body, "requested_by": user.email if user else None},
        response_payload_json={},
        last_error=None,
        attempt_count=0,
        queued_at=datetime.now(timezone.utc),
        last_attempted_at=None,
        sent_at=None,
        created_at=datetime.now(timezone.utc),
    )
    from app.tasks.notifications import send_external_notification_delivery

    send_external_notification_delivery.delay(str(delivery.id), trace_id)
    return delivery


def deliver_notification_delivery(db, delivery_id: str, trace_id: str | None = None) -> dict | None:
    repository = NotificationRepository(db)
    secret_store = get_secret_store()
    delivery = repository.get_delivery(UUID(delivery_id))
    if delivery is None or delivery.status == "sent":
        return None
    channel = repository.get_channel(delivery.organization_id, delivery.store_id, delivery.channel_id)
    if channel is None:
        repository.update_delivery(
            delivery,
            status="failed",
            attempt_count=delivery.attempt_count + 1,
            last_attempted_at=datetime.now(timezone.utc),
            last_error="Notification channel not found",
        )
        db.commit()
        return None
    notification = repository.get_notification(delivery.notification_id)
    if notification is None:
        repository.update_delivery(
            delivery,
            status="failed",
            attempt_count=delivery.attempt_count + 1,
            last_attempted_at=datetime.now(timezone.utc),
            last_error="Notification payload not found",
        )
        db.commit()
        return None
    payload = {
        "event_type": delivery.event_type,
        "notification_id": str(notification.id),
        "title": notification.title,
        "body": notification.body,
        "payload": notification.payload_json,
        "created_at": notification.created_at.isoformat(),
    }
    repository.update_delivery(
        delivery,
        trace_id=trace_id or delivery.trace_id,
        rendered_payload_json=payload,
        last_attempted_at=datetime.now(timezone.utc),
    )
    try:
        if channel.channel_type == "webhook":
            _send_webhook(channel.metadata_json, secret_store.get(channel.secret_reference) if channel.secret_reference else None, payload)
        elif channel.channel_type == "email":
            _send_email(channel.metadata_json, secret_store.get(channel.secret_reference) if channel.secret_reference else None, payload)
        else:
            raise ValueError(f"Unsupported channel type: {channel.channel_type}")
        repository.update_delivery(
            delivery,
            status="sent",
            trace_id=trace_id or delivery.trace_id,
            response_payload_json={"channel_type": channel.channel_type},
            sent_at=datetime.now(timezone.utc),
            attempt_count=delivery.attempt_count + 1,
            last_error=None,
            last_error_at=None,
            next_retry_at=None,
            terminal_failed_at=None,
        )
        repository.update_channel(
            channel,
            last_test_status="sent" if delivery.event_type == "manual_test" else channel.last_test_status,
            last_test_error=None if delivery.event_type == "manual_test" else channel.last_test_error,
            last_tested_at=datetime.now(timezone.utc) if delivery.event_type == "manual_test" else channel.last_tested_at,
        )
        db.commit()
        return {"status": "sent", "delivery_id": str(delivery.id)}
    except Exception as exc:  # noqa: BLE001
        message = redact_text(str(exc))
        repository.update_delivery(
            delivery,
            status="failed",
            trace_id=trace_id or delivery.trace_id,
            last_error=message,
            attempt_count=delivery.attempt_count + 1,
            last_attempted_at=datetime.now(timezone.utc),
            last_error_at=datetime.now(timezone.utc),
        )
        if delivery.event_type == "manual_test":
            repository.update_channel(
                channel,
                last_test_status="failed",
                last_test_error=message,
                last_tested_at=datetime.now(timezone.utc),
            )
        db.commit()
        raise


def _send_webhook(metadata_json: dict, secret_value: str | None, payload: dict) -> None:
    target_url = metadata_json.get("target_url")
    if not target_url:
        raise ValueError("Webhook target_url is required")
    headers = {"Content-Type": "application/json"}
    if secret_value:
        header_name = metadata_json.get("secret_header_name") or "Authorization"
        headers[header_name] = secret_value
    response = httpx.post(target_url, json=payload, headers=headers, timeout=10.0)
    response.raise_for_status()


def _send_email(metadata_json: dict, secret_value: str | None, payload: dict) -> None:
    smtp_host = metadata_json.get("smtp_host")
    smtp_port = int(metadata_json.get("smtp_port", 587))
    smtp_username = metadata_json.get("smtp_username")
    from_email = metadata_json.get("from_email")
    to_email = metadata_json.get("to_email")
    if not smtp_host or not from_email or not to_email:
        raise ValueError("smtp_host, from_email, and to_email are required")
    message = EmailMessage()
    message["Subject"] = payload["title"]
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(payload["body"])
    use_tls = bool(metadata_json.get("use_tls", True))
    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
        if use_tls:
            smtp.starttls()
        if smtp_username and secret_value:
            smtp.login(smtp_username, secret_value)
        smtp.send_message(message)


def mask_channel_metadata(channel_type: str, metadata_json: dict) -> dict:
    if channel_type == "webhook":
        target_url = metadata_json.get("target_url")
        return {
            "target_url": target_url,
            "target_host": urlparse(target_url).netloc if target_url else None,
            "secret_header_name": metadata_json.get("secret_header_name"),
        }
    if channel_type == "email":
        return {
            "smtp_host": metadata_json.get("smtp_host"),
            "smtp_port": metadata_json.get("smtp_port"),
            "smtp_username": metadata_json.get("smtp_username"),
            "from_email": metadata_json.get("from_email"),
            "to_email": metadata_json.get("to_email"),
            "use_tls": metadata_json.get("use_tls", True),
        }
    return metadata_json
