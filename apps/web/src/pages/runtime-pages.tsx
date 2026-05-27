import { useState } from "react";
import { useSearchParams, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { runtimeApi } from "@frontend/api-client";
import { Input } from "@frontend/ui";
import {
  DetailPanel,
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  PageHeader,
  RuntimeRunCard,
  SectionCard
} from "@/components/common";
import { formatDate, formatJson } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

export function RuntimeWorkflowRunsPage() {
  const { storeId = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [statusFilter, setStatusFilter] = useState("");
  const selectedId = searchParams.get("run");

  const listQuery = useQuery({
    queryKey: ["runtime", "workflows", storeId, statusFilter],
    queryFn: () => runtimeApi.listWorkflowRuns(storeId, { status: statusFilter || undefined }),
    enabled: Boolean(storeId)
  });

  const detailQuery = useQuery({
    queryKey: ["runtime", "workflow", storeId, selectedId],
    queryFn: () => runtimeApi.getWorkflowRun(storeId, selectedId!),
    enabled: Boolean(storeId && selectedId)
  });

  const runs = listQuery.data ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Workflow runs"
        description="Inspect store-scoped workflow execution history for sync, support drafting, approvals, and downstream operations."
        actions={<Input value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} placeholder="Filter by status" />}
      />

      {listQuery.isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : listQuery.isError ? (
        <ErrorState title="Could not load workflow runs" message={messageFromError(listQuery.error)} />
      ) : runs.length === 0 ? (
        <EmptyState title="No workflow runs" message="Once system workflows execute for this store, they will appear here." />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <SectionCard title="Recent workflow runs">
            <div className="space-y-3">
              {runs.map((run) => (
                <button
                  key={run.id}
                  className="w-full text-left"
                  onClick={() => setSearchParams(run.id === selectedId ? {} : { run: run.id })}
                >
                  <RuntimeRunCard
                    title={run.trigger_type}
                    status={run.status}
                    meta={`Created ${formatDate(run.created_at)}`}
                    body={run.error_message ? <span className="text-rose-700">{run.error_message}</span> : undefined}
                  />
                </button>
              ))}
            </div>
          </SectionCard>

          {selectedId ? (
            detailQuery.isLoading ? (
              <LoadingSkeleton rows={4} />
            ) : detailQuery.isError || !detailQuery.data ? (
              <ErrorState title="Could not load workflow detail" message={messageFromError(detailQuery.error)} />
            ) : (
              <SectionCard title="Workflow run detail">
                <div className="space-y-4 text-sm text-slate-700">
                  <p><span className="font-semibold text-slate-950">Workflow ID:</span> {detailQuery.data.workflow_id ?? "Unlinked"}</p>
                  <p><span className="font-semibold text-slate-950">Created:</span> {formatDate(detailQuery.data.created_at)}</p>
                  <p><span className="font-semibold text-slate-950">Input payload</span></p>
                  <pre className="whitespace-pre-wrap rounded-2xl border border-slate-200 bg-slate-50 p-4">{formatJson(detailQuery.data.input_payload ?? {})}</pre>
                  <p><span className="font-semibold text-slate-950">Output payload</span></p>
                  <pre className="whitespace-pre-wrap rounded-2xl border border-slate-200 bg-slate-50 p-4">{formatJson(detailQuery.data.output_payload ?? {})}</pre>
                </div>
              </SectionCard>
            )
          ) : (
            <DetailPanel title="Select a workflow run" subtitle="Choose a run to inspect payloads and failure details." />
          )}
        </div>
      )}
    </div>
  );
}

export function RuntimeAgentRunsPage() {
  const { storeId = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [agentType, setAgentType] = useState("");
  const selectedId = searchParams.get("run");

  const listQuery = useQuery({
    queryKey: ["runtime", "agents", storeId, agentType],
    queryFn: () => runtimeApi.listAgentRuns(storeId, { agent_type: agentType || undefined }),
    enabled: Boolean(storeId)
  });

  const detailQuery = useQuery({
    queryKey: ["runtime", "agent", storeId, selectedId],
    queryFn: () => runtimeApi.getAgentRun(storeId, selectedId!),
    enabled: Boolean(storeId && selectedId)
  });

  const runs = listQuery.data ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Agent runs"
        description="Track structured generation executions, model usage, retrieval summaries, and failure states."
        actions={<Input value={agentType} onChange={(event) => setAgentType(event.target.value)} placeholder="Filter by agent type" />}
      />

      {listQuery.isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : listQuery.isError ? (
        <ErrorState title="Could not load agent runs" message={messageFromError(listQuery.error)} />
      ) : runs.length === 0 ? (
        <EmptyState title="No agent runs" message="Agent-assisted workflows will appear once drafts and recommendations have been generated." />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <SectionCard title="Recent agent runs">
            <div className="space-y-3">
              {runs.map((run) => (
                <button key={run.id} className="w-full text-left" onClick={() => setSearchParams(run.id === selectedId ? {} : { run: run.id })}>
                  <RuntimeRunCard
                    title={run.agent_type}
                    status={run.status}
                    meta={`${run.model_name} · ${formatDate(run.created_at)}`}
                    body={run.output_summary ?? run.input_summary ?? undefined}
                  />
                </button>
              ))}
            </div>
          </SectionCard>

          {selectedId ? (
            detailQuery.isLoading ? (
              <LoadingSkeleton rows={4} />
            ) : detailQuery.isError || !detailQuery.data ? (
              <ErrorState title="Could not load agent detail" message={messageFromError(detailQuery.error)} />
            ) : (
              <SectionCard title="Agent run detail">
                <div className="space-y-4 text-sm text-slate-700">
                  <p><span className="font-semibold text-slate-950">Workflow run:</span> {detailQuery.data.workflow_run_id ?? "Unlinked"}</p>
                  <p><span className="font-semibold text-slate-950">Input summary:</span> {detailQuery.data.input_summary ?? "n/a"}</p>
                  <p><span className="font-semibold text-slate-950">Retrieved context:</span> {detailQuery.data.retrieved_context_summary ?? "n/a"}</p>
                  <p><span className="font-semibold text-slate-950">Output summary:</span> {detailQuery.data.output_summary ?? "n/a"}</p>
                  {detailQuery.data.error_message ? (
                    <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-800">{detailQuery.data.error_message}</div>
                  ) : null}
                </div>
              </SectionCard>
            )
          ) : (
            <DetailPanel title="Select an agent run" subtitle="Choose a run to inspect its summaries and linked workflow metadata." />
          )}
        </div>
      )}
    </div>
  );
}

export function RuntimeAuditPage() {
  const { storeId = "" } = useParams();
  const [entityType, setEntityType] = useState("");

  const auditQuery = useQuery({
    queryKey: ["runtime", "audit", storeId, entityType],
    queryFn: () => runtimeApi.listAuditEvents(storeId, { entity_type: entityType || undefined }),
    enabled: Boolean(storeId)
  });

  const events = auditQuery.data ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Audit trail"
        description="Review store-scoped audit events created by approvals, fraud decisions, workflows, and operator actions."
        actions={<Input value={entityType} onChange={(event) => setEntityType(event.target.value)} placeholder="Filter by entity type" />}
      />

      {auditQuery.isLoading ? (
        <LoadingSkeleton rows={6} />
      ) : auditQuery.isError ? (
        <ErrorState title="Could not load audit events" message={messageFromError(auditQuery.error)} />
      ) : events.length === 0 ? (
        <EmptyState title="No audit events yet" message="Once operators and workflows mutate tracked entities, audit events will appear here." />
      ) : (
        <SectionCard title="Recent audit events">
          <div className="space-y-3">
            {events.map((event) => (
              <RuntimeRunCard
                key={event.id}
                title={`${event.entity_type} · ${event.action_type}`}
                status={event.outcome}
                meta={`${event.source_type} · ${formatDate(event.created_at)}`}
                body={
                  <div className="space-y-2">
                    <p>User: {event.user_id ?? "system"}</p>
                    {event.metadata_json ? (
                      <pre className="whitespace-pre-wrap rounded-2xl border border-slate-200 bg-slate-50 p-4">{formatJson(event.metadata_json)}</pre>
                    ) : null}
                  </div>
                }
              />
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}
