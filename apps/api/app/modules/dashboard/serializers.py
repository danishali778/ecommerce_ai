def serialize_workflow_run(run) -> dict:
    return {
        "id": str(run.id),
        "status": run.status,
        "trigger_type": run.trigger_type,
        "workflow_id": str(run.workflow_id) if run.workflow_id else None,
        "created_at": run.created_at.isoformat(),
        "input_payload": run.input_payload,
        "output_payload": run.output_payload,
        "error_message": run.error_message,
    }


def serialize_agent_run(run) -> dict:
    return {
        "id": str(run.id),
        "status": run.status,
        "agent_type": run.agent_type,
        "model_name": run.model_name,
        "created_at": run.created_at.isoformat(),
        "workflow_run_id": str(run.workflow_run_id) if run.workflow_run_id else None,
        "input_summary": run.input_summary,
        "retrieved_context_summary": run.retrieved_context_summary,
        "output_summary": run.output_summary,
        "error_message": run.error_message,
    }


def serialize_audit_event(event) -> dict:
    return {
        "id": str(event.id),
        "entity_type": event.entity_type,
        "action_type": event.action_type,
        "source_type": event.source_type,
        "outcome": event.outcome,
        "created_at": event.created_at.isoformat(),
        "user_id": str(event.user_id) if event.user_id else None,
        "metadata_json": event.metadata_json,
    }

