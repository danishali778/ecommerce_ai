from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_context
from app.api.deps.db import get_db
from app.api.schemas.common import SuccessEnvelope
from app.api.schemas.support import (
    SupportConversationCreateRequest,
    SupportConversationResponse,
    SupportConversationStatusUpdateRequest,
    SupportDraftGenerationAcceptedResponse,
    SupportMessageCreateRequest,
    SupportMessageResponse,
    SupportReplyDraftGenerateRequest,
)
from app.core.runtime import call_with_optional_trace
from app.core.responses import success_response
from app.services.support import SupportService


router = APIRouter()


def get_support_service(db: Session = Depends(get_db)) -> SupportService:
    return SupportService(db)


@router.post(
    "/{store_id}/support/conversations",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[SupportConversationResponse],
    summary="Create support conversation",
)
def create_support_conversation(
    store_id: UUID,
    payload: SupportConversationCreateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: SupportService = Depends(get_support_service),
):
    return success_response(request, service.create_conversation(user_context, store_id, payload))


@router.get(
    "/{store_id}/support/conversations",
    response_model=SuccessEnvelope[list[SupportConversationResponse]],
    summary="List support conversations",
)
def list_support_conversations(
    store_id: UUID,
    request: Request,
    status_filter: str | None = Query(default=None, alias="status"),
    user_context=Depends(get_current_user_context),
    service: SupportService = Depends(get_support_service),
):
    conversations = service.list_conversations(user_context, store_id, status=status_filter)
    return success_response(request, conversations, meta={"count": len(conversations)})


@router.get(
    "/{store_id}/support/conversations/{conversation_id}",
    response_model=SuccessEnvelope[SupportConversationResponse],
    summary="Get support conversation",
)
def get_support_conversation(
    store_id: UUID,
    conversation_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: SupportService = Depends(get_support_service),
):
    return success_response(request, service.get_conversation(user_context, store_id, conversation_id))


@router.patch(
    "/{store_id}/support/conversations/{conversation_id}",
    response_model=SuccessEnvelope[SupportConversationResponse],
    summary="Update support conversation status",
)
def update_support_conversation(
    store_id: UUID,
    conversation_id: UUID,
    payload: SupportConversationStatusUpdateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: SupportService = Depends(get_support_service),
):
    return success_response(request, service.update_conversation_status(user_context, store_id, conversation_id, payload))


@router.post(
    "/{store_id}/support/conversations/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[SupportMessageResponse],
    summary="Create support message",
)
def create_support_message(
    store_id: UUID,
    conversation_id: UUID,
    payload: SupportMessageCreateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: SupportService = Depends(get_support_service),
):
    return success_response(request, service.create_message(user_context, store_id, conversation_id, payload))


@router.get(
    "/{store_id}/support/conversations/{conversation_id}/messages",
    response_model=SuccessEnvelope[list[SupportMessageResponse]],
    summary="List support messages",
)
def list_support_messages(
    store_id: UUID,
    conversation_id: UUID,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: SupportService = Depends(get_support_service),
):
    messages = service.list_messages(user_context, store_id, conversation_id)
    return success_response(request, messages, meta={"count": len(messages)})


@router.post(
    "/{store_id}/support/conversations/{conversation_id}/reply-drafts/generate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessEnvelope[SupportDraftGenerationAcceptedResponse],
    summary="Generate support reply draft",
)
def generate_support_reply_draft(
    store_id: UUID,
    conversation_id: UUID,
    payload: SupportReplyDraftGenerateRequest,
    request: Request,
    user_context=Depends(get_current_user_context),
    service: SupportService = Depends(get_support_service),
):
    return success_response(
        request,
        call_with_optional_trace(
            service.generate_reply_draft,
            user_context,
            store_id,
            conversation_id,
            payload,
            trace_id=request.state.request_id,
        ),
    )
