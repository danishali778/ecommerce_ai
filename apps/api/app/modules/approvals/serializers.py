def serialize_approval(approval) -> dict:
    return {
        "id": str(approval.id),
        "status": approval.status,
        "action_type": approval.action_type,
        "entity_type": approval.entity_type,
        "entity_id": str(approval.entity_id),
        "reasoning": approval.reasoning,
        "review_notes": approval.review_notes,
        "execution_status": approval.execution_status,
        "execution_error": approval.execution_error,
        "expires_at": approval.expires_at.isoformat(),
        "created_at": approval.created_at.isoformat(),
        "updated_at": approval.updated_at.isoformat(),
    }

