from uuid import UUID

from sqlalchemy import select

from app.repositories.base import Repository
from app.repositories.models import AgentRun, AuditEvent, Notification, Workflow, WorkflowRun


class WorkflowRepository(Repository):
    def get_workflow_by_key(self, key: str) -> Workflow | None:
        return self.db.scalar(select(Workflow).where(Workflow.key == key))

    def ensure_system_workflow(
        self,
        *,
        key: str,
        name: str,
        phase_scope: str,
        trigger_type: str,
        action_type: str,
        approval_required: bool = False,
        condition_json: dict | None = None,
        is_active: bool = True,
    ) -> Workflow:
        workflow = self.get_workflow_by_key(key)
        if workflow is not None:
            return workflow
        workflow = Workflow(
            organization_id=None,
            name=name,
            key=key,
            phase_scope=phase_scope,
            trigger_type=trigger_type,
            condition_json=condition_json or {},
            action_type=action_type,
            approval_required=approval_required,
            is_system_defined=True,
            is_active=is_active,
        )
        self.db.add(workflow)
        self.db.flush()
        return workflow

    def create_workflow_run(self, **values) -> WorkflowRun:
        workflow_run = WorkflowRun(**values)
        self.db.add(workflow_run)
        self.db.flush()
        return workflow_run

    def update_workflow_run(self, workflow_run: WorkflowRun, **values) -> WorkflowRun:
        for key, value in values.items():
            setattr(workflow_run, key, value)
        self.db.flush()
        return workflow_run

    def list_workflow_runs(
        self,
        organization_id: UUID,
        store_id: UUID,
        *,
        status: str | None = None,
        workflow_key: str | None = None,
        trigger_type: str | None = None,
    ) -> list[WorkflowRun]:
        query = (
            select(WorkflowRun)
            .where(WorkflowRun.organization_id == organization_id, WorkflowRun.store_id == store_id)
            .order_by(WorkflowRun.created_at.desc())
        )
        if status:
            query = query.where(WorkflowRun.status == status)
        if workflow_key:
            workflow = self.get_workflow_by_key(workflow_key)
            query = query.where(WorkflowRun.workflow_id == workflow.id if workflow else None)
        if trigger_type:
            query = query.where(WorkflowRun.trigger_type == trigger_type)
        return list(self.db.scalars(query))

    def get_workflow_run(self, organization_id: UUID, store_id: UUID, workflow_run_id: UUID) -> WorkflowRun | None:
        return self.db.scalar(
            select(WorkflowRun).where(
                WorkflowRun.organization_id == organization_id,
                WorkflowRun.store_id == store_id,
                WorkflowRun.id == workflow_run_id,
            )
        )

    def create_agent_run(self, **values) -> AgentRun:
        agent_run = AgentRun(**values)
        self.db.add(agent_run)
        self.db.flush()
        return agent_run

    def update_agent_run(self, agent_run: AgentRun, **values) -> AgentRun:
        for key, value in values.items():
            setattr(agent_run, key, value)
        self.db.flush()
        return agent_run

    def list_agent_runs(
        self,
        organization_id: UUID,
        store_id: UUID,
        *,
        agent_type: str | None = None,
        status: str | None = None,
        workflow_run_id: UUID | None = None,
    ) -> list[AgentRun]:
        query = (
            select(AgentRun)
            .where(AgentRun.organization_id == organization_id, AgentRun.store_id == store_id)
            .order_by(AgentRun.created_at.desc())
        )
        if agent_type:
            query = query.where(AgentRun.agent_type == agent_type)
        if status:
            query = query.where(AgentRun.status == status)
        if workflow_run_id:
            query = query.where(AgentRun.workflow_run_id == workflow_run_id)
        return list(self.db.scalars(query))

    def get_agent_run(self, organization_id: UUID, store_id: UUID, agent_run_id: UUID) -> AgentRun | None:
        return self.db.scalar(
            select(AgentRun).where(
                AgentRun.organization_id == organization_id,
                AgentRun.store_id == store_id,
                AgentRun.id == agent_run_id,
            )
        )

    def create_audit_event(self, **values) -> AuditEvent:
        audit_event = AuditEvent(**values)
        self.db.add(audit_event)
        self.db.flush()
        return audit_event

    def list_audit_events(
        self,
        organization_id: UUID,
        store_id: UUID,
        *,
        entity_type: str | None = None,
        action_type: str | None = None,
        user_id: UUID | None = None,
    ) -> list[AuditEvent]:
        query = (
            select(AuditEvent)
            .where(AuditEvent.organization_id == organization_id, AuditEvent.store_id == store_id)
            .order_by(AuditEvent.created_at.desc())
        )
        if entity_type:
            query = query.where(AuditEvent.entity_type == entity_type)
        if action_type:
            query = query.where(AuditEvent.action_type == action_type)
        if user_id:
            query = query.where(AuditEvent.user_id == user_id)
        return list(self.db.scalars(query))

    def create_notification(self, **values) -> Notification:
        notification = Notification(**values)
        self.db.add(notification)
        self.db.flush()
        return notification

    def list_notifications(self, organization_id: UUID, user_id: UUID) -> list[Notification]:
        return list(
            self.db.scalars(
                select(Notification)
                .where(Notification.organization_id == organization_id, Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
            )
        )
