from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from app.agents.support.prompts import build_support_reply_prompt
from app.agents.support.schemas import SupportAgentOutput
from app.core.redaction import redact_text
from app.core.settings import get_settings
from app.llm.provider import LLMProvider
from app.modules.policies.module import infer_policy_document_type, retrieve_relevant_chunks, serialize_chunk
from app.repositories.policy_repository import PolicyRepository
from app.repositories.support_repository import SupportRepository
from app.repositories.sync_repository import SyncRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.repositories.models import AgentRun, SupportConversation, WorkflowRun


class SupportAgentRunner:
    def __init__(self, db) -> None:
        self.db = db
        self.support_repository = SupportRepository(db)
        self.policy_repository = PolicyRepository(db)
        self.sync_repository = SyncRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.llm_provider = LLMProvider()

    def start_generation(
        self,
        *,
        organization_id: UUID,
        store_id: UUID,
        user_id: UUID,
        conversation: SupportConversation,
        trace_id: str | None = None,
    ) -> dict:
        workflow = self.workflow_repository.ensure_system_workflow(
            key="support_reply_draft_generated",
            name="Support Reply Draft Generated",
            phase_scope="p1",
            trigger_type="support_reply_draft_generated",
            action_type="support_draft_saved_and_logged",
        )
        workflow_run = self.workflow_repository.create_workflow_run(
            organization_id=organization_id,
            store_id=store_id,
            workflow_id=workflow.id,
            trigger_type="support_reply_draft_generated",
            trigger_entity_type="support_conversation",
            trigger_entity_id=conversation.id,
            status="queued",
            trace_id=trace_id,
            input_payload={"conversation_id": str(conversation.id)},
            output_payload={},
        )
        agent_run = self.workflow_repository.create_agent_run(
            organization_id=organization_id,
            store_id=store_id,
            agent_type="support_reply",
            user_id=user_id,
            workflow_run_id=workflow_run.id,
            input_summary=f"Generate support reply draft for conversation {conversation.id}",
            retrieved_context_summary=None,
            output_summary=None,
            tool_calls_json=[],
            model_name=self.llm_provider.model,
            status="queued",
            trace_id=trace_id,
        )
        return {
            "workflow_run_id": str(workflow_run.id),
            "agent_run_id": str(agent_run.id),
            "status": workflow_run.status,
        }

    def execute_generation(self, agent_run_id: str, trace_id: str | None = None) -> dict | None:
        agent_run = self.db.get(AgentRun, UUID(agent_run_id))
        if agent_run is None:
            return None
        workflow_run = self.db.get(WorkflowRun, agent_run.workflow_run_id) if agent_run.workflow_run_id else None
        conversation_id = (workflow_run.input_payload or {}).get("conversation_id") if workflow_run else None
        conversation = self.db.get(SupportConversation, UUID(conversation_id)) if conversation_id else None
        if workflow_run is None or conversation is None:
            self._mark_failed(agent_run, workflow_run, "Support draft context is incomplete")
            self.db.commit()
            return None

        try:
            now = datetime.now(timezone.utc)
            self.workflow_repository.update_agent_run(agent_run, status="running", trace_id=trace_id or agent_run.trace_id)
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="running",
                trace_id=trace_id or workflow_run.trace_id,
                started_at=workflow_run.started_at or now,
            )
            messages = self.support_repository.list_messages(conversation.organization_id, conversation.store_id, conversation.id)
            conversation_payload = [
                {"direction": message.direction, "body": message.body, "status": message.status}
                for message in messages
            ]
            latest_question = next((message.body for message in reversed(messages) if message.direction == "inbound"), "")
            customer = (
                self.sync_repository.get_customer(conversation.organization_id, conversation.store_id, conversation.customer_id)
                if conversation.customer_id
                else None
            )
            order = (
                self.sync_repository.get_order(conversation.organization_id, conversation.store_id, conversation.order_id)
                if conversation.order_id
                else None
            )
            document_type = infer_policy_document_type(latest_question)
            retrieved_chunks = retrieve_relevant_chunks(
                self.policy_repository,
                self.llm_provider,
                conversation.organization_id,
                conversation.store_id,
                latest_question or "general support policy",
                document_type=document_type,
                top_k=get_settings().rag_max_prompt_chunks,
            )
            retrieved_payload = [serialize_chunk(chunk) for chunk in retrieved_chunks]
            output = self._generate_output(
                conversation_messages=conversation_payload,
                customer_context={
                    "email": customer.email,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "total_orders": customer.total_orders,
                }
                if customer
                else None,
                order_context={
                    "external_order_id": order.external_order_id,
                    "status": order.status,
                    "payment_status": order.payment_status,
                    "fulfillment_status": order.fulfillment_status,
                    "total": str(order.total),
                    "currency": order.currency,
                }
                if order
                else None,
                policy_chunks=retrieved_payload,
            )
            threshold = get_settings().support_policy_confidence_threshold
            needs_human_review = output.needs_human_review or output.confidence_score < threshold or not retrieved_payload
            review_reason_code = output.review_reason_code
            if not retrieved_payload and not review_reason_code:
                review_reason_code = "missing_policy_context"
            elif output.confidence_score < threshold and not review_reason_code:
                review_reason_code = "low_confidence"
            message = self.support_repository.create_message(
                organization_id=conversation.organization_id,
                store_id=conversation.store_id,
                conversation_id=conversation.id,
                direction="draft_outbound",
                body=output.draft_body,
                generated_by_ai=True,
                confidence_score=output.confidence_score,
                needs_human_review=needs_human_review,
                review_reason_code=review_reason_code,
                status="pending_review" if needs_human_review else "draft_ready",
                cited_policy_chunks_json=[citation.model_dump() for citation in output.cited_policy_chunks],
                cited_order_facts_summary=output.cited_order_facts_summary,
                created_by_user_id=agent_run.user_id,
            )
            self.support_repository.update_conversation(
                conversation,
                status="pending_review" if needs_human_review else conversation.status,
            )
            self.workflow_repository.update_agent_run(
                agent_run,
                status="succeeded",
                trace_id=trace_id or agent_run.trace_id,
                retrieved_context_summary="\n\n".join(chunk["content"] for chunk in retrieved_payload),
                output_summary=redact_text(output.draft_body),
            )
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="succeeded",
                trace_id=trace_id or workflow_run.trace_id,
                output_payload={"support_message_id": str(message.id)},
                completed_at=datetime.now(timezone.utc),
            )
            self.db.commit()
            return {
                "support_message_id": str(message.id),
                "workflow_run_id": str(workflow_run.id),
                "agent_run_id": str(agent_run.id),
                "status": message.status,
            }
        except Exception as exc:  # noqa: BLE001
            self._mark_failed(agent_run, workflow_run, str(exc))
            self.db.commit()
            raise

    def _generate_output(
        self,
        *,
        conversation_messages: list[dict],
        customer_context: dict | None,
        order_context: dict | None,
        policy_chunks: list[dict],
    ) -> SupportAgentOutput:
        def generate_node(state: dict) -> dict:
            prompt = build_support_reply_prompt(
                conversation_messages=state["conversation_messages"],
                customer_context=state["customer_context"],
                order_context=state["order_context"],
                policy_chunks=state["policy_chunks"],
            )
            raw = self.llm_provider.generate_structured_json(prompt)
            output = SupportAgentOutput.model_validate(raw)
            return {"result": output}

        graph = StateGraph(dict)
        graph.add_node("generate", generate_node)
        graph.add_edge(START, "generate")
        graph.add_edge("generate", END)
        result = graph.compile().invoke(
            {
                "conversation_messages": conversation_messages,
                "customer_context": customer_context,
                "order_context": order_context,
                "policy_chunks": policy_chunks,
            }
        )
        return result["result"]

    def _mark_failed(self, agent_run: AgentRun, workflow_run: WorkflowRun | None, message: str) -> None:
        redacted = redact_text(message)
        self.workflow_repository.update_agent_run(agent_run, status="failed", error_message=redacted)
        if workflow_run is not None:
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="failed",
                error_message=redacted,
                completed_at=datetime.now(timezone.utc),
            )
