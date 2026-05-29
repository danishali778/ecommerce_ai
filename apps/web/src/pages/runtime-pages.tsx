import { useMemo, useState } from "react";
import { useSearchParams, useParams } from "react-router-dom";
import { Activity, Bot, History, Search } from "lucide-react";

import { Input } from "@frontend/ui";
import {
  DetailPanel,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
  MetricCard,
  PageHeader,
  RuntimeRunCard,
  SectionCard,
  StatusPill
} from "@/components/common";
import { useAgentRun, useAgentRuns, useAuditEvents, useWorkflowRun, useWorkflowRuns } from "@/hooks/use-runtime";
import { formatDate, formatJson, titleize } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function JsonCard({ title, value }: { title: string; value: unknown }) {
  return (
    <SectionCard title={title}>
      <pre className="whitespace-pre-wrap rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">{formatJson(value ?? {})}</pre>
    </SectionCard>
  );
}

export function RuntimeWorkflowRunsPage() {
  const { storeId = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [statusFilter, setStatusFilter] = useState("");
  const selectedId = searchParams.get("run");

  const listQuery = useWorkflowRuns(storeId, { status: statusFilter || undefined });
  const detailQuery = useWorkflowRun(storeId, selectedId);

  const runs = listQuery.data ?? [];
  const succeededCount = runs.filter((run) => run.status === "succeeded").length;
  const failedCount = runs.filter((run) => run.status === "failed").length;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Workflow runs"
        description="Inspect store-scoped workflow execution for sync, drafting, approvals, and downstream operations."
        actions={
          <div className="relative min-w-56">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input className="pl-9" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} placeholder="Filter by status" />
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Runs" value={runs.length} hint="Workflow executions returned for this store" />
        <MetricCard label="Succeeded" value={succeededCount} hint="Completed without downstream error" tone={succeededCount ? "success" : "neutral"} />
        <MetricCard label="Failed" value={failedCount} hint="Needs audit or retry investigation" tone={failedCount ? "danger" : "success"} />
      </div>

      {listQuery.isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : listQuery.isError ? (
        <ErrorState title="Could not load workflow runs" message={messageFromError(listQuery.error)} />
      ) : runs.length === 0 ? (
        <EmptyState title="No workflow runs" message="Once system workflows execute for this store, they will appear here." />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[0.84fr_1.16fr]">
          <SectionCard title="Recent workflow runs">
            <div className="space-y-3">
              {runs.map((run) => (
                <button
                  key={run.id}
                  className="w-full text-left"
                  onClick={() => setSearchParams(run.id === selectedId ? {} : { run: run.id })}
                >
                  <RuntimeRunCard
                    title={titleize(run.trigger_type)}
                    status={run.status}
                    meta={`Created ${formatDate(run.created_at)}`}
                    body={run.error_message ? <span className="text-rose-700">{run.error_message}</span> : "Inspect input/output payloads and linked workflow metadata."}
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
              <div className="space-y-6">
                <DetailPanel title="Workflow run detail" subtitle="Traceable execution metadata for the selected workflow run">
                  <KeyValueGrid
                    items={[
                      { label: "Run ID", value: detailQuery.data.id },
                      { label: "Status", value: <StatusPill value={detailQuery.data.status} /> },
                      { label: "Workflow ID", value: detailQuery.data.workflow_id ?? "Unlinked" },
                      { label: "Created", value: formatDate(detailQuery.data.created_at) }
                    ]}
                  />
                </DetailPanel>

                {detailQuery.data.error_message ? (
                  <ErrorState title="Workflow execution error" message={detailQuery.data.error_message} />
                ) : null}

                <JsonCard title="Input payload" value={detailQuery.data.input_payload ?? {}} />
                <JsonCard title="Output payload" value={detailQuery.data.output_payload ?? {}} />
              </div>
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

  const listQuery = useAgentRuns(storeId, { agent_type: agentType || undefined });
  const detailQuery = useAgentRun(storeId, selectedId);

  const runs = listQuery.data ?? [];
  const healthyCount = runs.filter((run) => run.status === "succeeded").length;
  const failedCount = runs.filter((run) => run.status === "failed").length;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Agent runs"
        description="Track structured generation executions, model usage, retrieval summaries, and reviewable failure states."
        actions={
          <div className="relative min-w-56">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input className="pl-9" value={agentType} onChange={(event) => setAgentType(event.target.value)} placeholder="Filter by agent type" />
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Agent Runs" value={runs.length} hint="Structured generation and recommendation runs" />
        <MetricCard label="Healthy" value={healthyCount} hint="Succeeded agent runs in the current store" tone={healthyCount ? "success" : "neutral"} />
        <MetricCard label="Failed" value={failedCount} hint="Runs that need investigation or retry" tone={failedCount ? "danger" : "success"} />
      </div>

      {listQuery.isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : listQuery.isError ? (
        <ErrorState title="Could not load agent runs" message={messageFromError(listQuery.error)} />
      ) : runs.length === 0 ? (
        <EmptyState title="No agent runs" message="Agent-assisted workflows will appear once drafts and recommendations have been generated." />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[0.84fr_1.16fr]">
          <SectionCard title="Recent agent runs">
            <div className="space-y-3">
              {runs.map((run) => (
                <button key={run.id} className="w-full text-left" onClick={() => setSearchParams(run.id === selectedId ? {} : { run: run.id })}>
                  <RuntimeRunCard
                    title={titleize(run.agent_type)}
                    status={run.status}
                    meta={`${run.model_name} - ${formatDate(run.created_at)}`}
                    body={run.output_summary ?? run.input_summary ?? "Inspect context summaries and linked workflow metadata."}
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
              <div className="space-y-6">
                <DetailPanel title="Agent run detail" subtitle="Review model usage, summaries, and linked workflow context">
                  <KeyValueGrid
                    items={[
                      { label: "Run ID", value: detailQuery.data.id },
                      { label: "Status", value: <StatusPill value={detailQuery.data.status} /> },
                      { label: "Agent type", value: titleize(detailQuery.data.agent_type) },
                      { label: "Model", value: detailQuery.data.model_name },
                      { label: "Workflow run", value: detailQuery.data.workflow_run_id ?? "Unlinked" },
                      { label: "Created", value: formatDate(detailQuery.data.created_at) }
                    ]}
                  />
                </DetailPanel>

                <SectionCard title="Summaries">
                  <div className="space-y-4 text-sm text-slate-700">
                    <div>
                      <p className="font-semibold text-slate-950">Input summary</p>
                      <p className="mt-1 leading-7">{detailQuery.data.input_summary ?? "No summary captured."}</p>
                    </div>
                    <div>
                      <p className="font-semibold text-slate-950">Retrieved context</p>
                      <p className="mt-1 leading-7">{detailQuery.data.retrieved_context_summary ?? "No retrieved-context summary captured."}</p>
                    </div>
                    <div>
                      <p className="font-semibold text-slate-950">Output summary</p>
                      <p className="mt-1 leading-7">{detailQuery.data.output_summary ?? "No output summary captured."}</p>
                    </div>
                  </div>
                </SectionCard>

                {detailQuery.data.error_message ? <ErrorState title="Agent run error" message={detailQuery.data.error_message} /> : null}
              </div>
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

  const auditQuery = useAuditEvents(storeId, { entity_type: entityType || undefined });

  const events = auditQuery.data ?? [];
  const outcomeCounts = useMemo(() => {
    return {
      success: events.filter((event) => event.outcome === "success").length,
      failed: events.filter((event) => event.outcome === "failed").length,
      total: events.length
    };
  }, [events]);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Audit trail"
        description="Review store-scoped audit events created by approvals, fraud decisions, workflows, and operator actions."
        actions={
          <div className="relative min-w-56">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input className="pl-9" value={entityType} onChange={(event) => setEntityType(event.target.value)} placeholder="Filter by entity type" />
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Audit Events" value={outcomeCounts.total} hint="Tracked entity changes for the selected store" />
        <MetricCard label="Successful" value={outcomeCounts.success} hint="Events with successful outcomes" tone={outcomeCounts.success ? "success" : "neutral"} />
        <MetricCard label="Failed" value={outcomeCounts.failed} hint="Events that ended in failure or exception" tone={outcomeCounts.failed ? "danger" : "success"} />
      </div>

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
                title={`${titleize(event.entity_type)} - ${titleize(event.action_type)}`}
                status={event.outcome}
                meta={`${titleize(event.source_type)} - ${formatDate(event.created_at)}`}
                body={
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      <BadgeLike label={`User ${event.user_id ?? "system"}`} />
                      <BadgeLike label={`Event ${event.id}`} />
                    </div>
                    {event.metadata_json ? (
                      <pre className="whitespace-pre-wrap rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-700">
                        {formatJson(event.metadata_json)}
                      </pre>
                    ) : (
                      <p className="text-sm text-slate-600">No structured metadata captured for this event.</p>
                    )}
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

function BadgeLike({ label }: { label: string }) {
  return <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{label}</span>;
}
