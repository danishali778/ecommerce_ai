from __future__ import annotations

from uuid import UUID, uuid4


def emit_workflow_event(
    *,
    organization_id: UUID,
    store_id: UUID,
    trigger_type: str,
    entity_type: str,
    entity_id: UUID | None,
    payload: dict,
    trace_id: str | None = None,
) -> None:
    from app.tasks.workflows import evaluate_store_workflows

    evaluate_store_workflows.delay(
        str(organization_id),
        str(store_id),
        trigger_type,
        entity_type,
        str(entity_id) if entity_id else None,
        payload,
        str(uuid4()),
        trace_id,
    )
