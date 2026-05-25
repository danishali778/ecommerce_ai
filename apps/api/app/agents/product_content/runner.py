from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from app.agents.product_content.prompts import build_product_content_prompt
from app.agents.product_content.schemas import ProductContentAgentOutput
from app.core.redaction import redact_text
from app.llm.provider import LLMProvider
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.models import AgentRun, Product, WorkflowRun
from app.repositories.workflow_repository import WorkflowRepository


class ProductContentAgentRunner:
    def __init__(self, db) -> None:
        self.db = db
        self.catalog_repository = CatalogRepository(db)
        self.workflow_repository = WorkflowRepository(db)
        self.llm_provider = LLMProvider()

    def start_generation(
        self,
        organization_id: UUID,
        store_id: UUID,
        user_id: UUID,
        product: Product,
        generation_targets: list[str],
        tone: str,
        constraints: dict,
    ) -> dict:
        workflow = self.workflow_repository.get_workflow_by_key("product_content_generated")
        workflow_run = self.workflow_repository.create_workflow_run(
            organization_id=organization_id,
            store_id=store_id,
            workflow_id=workflow.id if workflow else None,
            trigger_type="product_content_generated",
            trigger_entity_type="product",
            trigger_entity_id=product.id,
            status="queued",
            input_payload={
                "product_id": str(product.id),
                "targets": generation_targets,
                "tone": tone,
                "constraints": constraints,
            },
            output_payload={},
        )
        agent_run = self.workflow_repository.create_agent_run(
            organization_id=organization_id,
            store_id=store_id,
            agent_type="product_content",
            user_id=user_id,
            workflow_run_id=workflow_run.id,
            input_summary=f"Generate draft for product {product.id}",
            retrieved_context_summary=product.description or "",
            output_summary=None,
            tool_calls_json=[],
            model_name=self.llm_provider.model,
            status="queued",
        )
        return {
            "workflow_run_id": str(workflow_run.id),
            "agent_run_id": str(agent_run.id),
            "status": workflow_run.status,
        }

    def execute_generation(self, agent_run_id: str) -> dict | None:
        agent_run = self.db.get(AgentRun, UUID(agent_run_id))
        if agent_run is None:
            return None
        workflow_run = self.db.get(WorkflowRun, agent_run.workflow_run_id) if agent_run.workflow_run_id else None
        if agent_run.status == "succeeded" and workflow_run is not None:
            return {
                "draft_id": (workflow_run.output_payload or {}).get("draft_id"),
                "workflow_run_id": str(workflow_run.id),
                "agent_run_id": str(agent_run.id),
                "status": "draft",
            }
        product_id = (workflow_run.input_payload or {}).get("product_id") if workflow_run else None
        product = self.db.get(Product, UUID(product_id)) if product_id else None
        if workflow_run is None or product is None:
            self._mark_failed(agent_run, workflow_run, "Draft generation context is incomplete")
            self.db.commit()
            return None
        try:
            now = datetime.now(timezone.utc)
            self.workflow_repository.update_agent_run(agent_run, status="running")
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="running",
                started_at=workflow_run.started_at or now,
            )
            output = self._generate_output(
                product=product,
                generation_targets=(workflow_run.input_payload or {}).get("targets", []),
                tone=(workflow_run.input_payload or {}).get("tone", "clear_and_premium"),
                constraints=(workflow_run.input_payload or {}).get("constraints", {}),
            )
            draft = self.catalog_repository.create_draft(
                organization_id=workflow_run.organization_id,
                store_id=workflow_run.store_id,
                product_id=product.id,
                source_snapshot_json={
                    "title": product.title,
                    "description": product.description,
                    "tags": product.tags,
                },
                generated_title=output.generated_title,
                generated_description=output.generated_description,
                generated_tags=output.generated_tags,
                generated_seo_title=output.generated_seo_title,
                generated_seo_description=output.generated_seo_description,
                generation_prompt_version="p0_v1",
                model_name=self.llm_provider.model,
                status="draft",
                created_by_user_id=agent_run.user_id,
            )
            self.workflow_repository.update_agent_run(
                agent_run,
                status="succeeded",
                output_summary=redact_text(output.reasoning),
            )
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="succeeded",
                output_payload={
                    "draft_id": str(draft.id),
                    "agent_run_id": str(agent_run.id),
                },
                completed_at=datetime.now(timezone.utc),
            )
            self.db.commit()
            return {
                "draft_id": str(draft.id),
                "workflow_run_id": str(workflow_run.id),
                "agent_run_id": str(agent_run.id),
                "status": draft.status,
            }
        except Exception as exc:  # noqa: BLE001
            self._mark_failed(agent_run, workflow_run, str(exc))
            self.db.commit()
            raise

    def _generate_output(
        self,
        *,
        product: Product,
        generation_targets: list[str],
        tone: str,
        constraints: dict,
    ) -> ProductContentAgentOutput:
        def generate_node(state: dict) -> dict:
            prompt = build_product_content_prompt(
                state["product"],
                state["generation_targets"],
                state["tone"],
                state["constraints"],
            )
            output = ProductContentAgentOutput.model_validate(self.llm_provider.generate_structured_json(prompt))
            return {"result": output}

        graph = StateGraph(dict)
        graph.add_node("generate", generate_node)
        graph.add_edge(START, "generate")
        graph.add_edge("generate", END)
        compiled = graph.compile()
        result = compiled.invoke(
            {
                "product": {
                    "title": product.title,
                    "handle": product.handle,
                    "vendor": product.vendor,
                    "category": product.category,
                    "description": product.description,
                    "tags": product.tags,
                },
                "generation_targets": generation_targets,
                "tone": tone,
                "constraints": constraints,
            }
        )
        return result["result"]

    def _mark_failed(self, agent_run: AgentRun, workflow_run: WorkflowRun | None, message: str) -> None:
        redacted = redact_text(message)
        self.workflow_repository.update_agent_run(
            agent_run,
            status="failed",
            error_message=redacted,
        )
        if workflow_run is not None:
            self.workflow_repository.update_workflow_run(
                workflow_run,
                status="failed",
                error_message=redacted,
                completed_at=datetime.now(timezone.utc),
            )
