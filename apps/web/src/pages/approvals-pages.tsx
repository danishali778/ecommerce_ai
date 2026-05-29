import * as React from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Clock3, Filter, RefreshCw, Search, XCircle } from "lucide-react";

import { approvalsApi } from "@frontend/api-client";
import { Button, Card, Checkbox, Input, Textarea } from "@frontend/ui";
import { useApproval, useApprovalActions, useApprovals } from "@/hooks/use-approvals";

import {
  DetailPanel,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
  MetricCard,
  PageHeader,
  ReviewRequiredBanner,
  SectionCard,
  StatusPill
} from "@/components/common";
import { formatDate, titleize } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function notesFromAction(action: string, selectionCount: number) {
  if (selectionCount === 1) return `${action} from approval queue`;
  return `${action} ${selectionCount} approval items from the queue`;
}

function matchesSearch(approval: Awaited<ReturnType<typeof approvalsApi.list>>[number], query: string) {
  if (!query) return true;
  const haystack = [approval.action_type, approval.entity_type, approval.entity_id, approval.reasoning, approval.review_notes ?? "", approval.status, approval.execution_status ?? ""]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query.toLowerCase());
}

function ApprovalQueueRow({
  approval,
  selected,
  onToggle
}: {
  approval: Awaited<ReturnType<typeof approvalsApi.list>>[number];
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <label
      className={`grid cursor-pointer gap-4 rounded-2xl border p-4 transition lg:grid-cols-[auto_1.3fr_0.95fr_0.8fr_0.8fr] ${
        selected ? "border-accent-300 bg-accent-50" : "border-slate-200 bg-white hover:border-accent-200"
      }`}
    >
      <div className="flex items-start gap-3">
        <Checkbox checked={selected} onChange={onToggle} />
        <div className="pt-0.5">
          <div className="flex items-center gap-2">
            <p className="font-semibold text-slate-950">{titleize(approval.action_type)}</p>
            <StatusPill value={approval.status} />
          </div>
          <p className="mt-2 text-sm text-slate-600">{approval.entity_type.replaceAll("_", " ")} · {approval.entity_id}</p>
        </div>
      </div>
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Context / details</p>
        <p className="text-sm leading-6 text-slate-700">{approval.reasoning}</p>
      </div>
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Execution</p>
        <StatusPill value={approval.execution_status ?? "not_started"} />
        {approval.execution_error ? <p className="text-xs text-rose-700">{approval.execution_error}</p> : null}
      </div>
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Created</p>
        <p className="text-sm text-slate-700">{formatDate(approval.created_at)}</p>
        <p className="text-xs text-slate-500">Expires {formatDate(approval.expires_at)}</p>
      </div>
      <div className="flex items-start justify-between gap-3 lg:justify-end">
        <div className="space-y-2 lg:text-right">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Open detail</p>
          <Link className="text-sm font-medium text-accent-600 hover:text-accent-700" to={`/app/approvals/${approval.id}`}>
            Inspect approval
          </Link>
        </div>
      </div>
    </label>
  );
}

export function ApprovalsPage() {
  const approvalsQuery = useApprovals();
  const navigate = useNavigate();
  const [search, setSearch] = React.useState("");
  const [selectedIds, setSelectedIds] = React.useState<string[]>([]);
  const [batchNotes, setBatchNotes] = React.useState("");

  const actionMutation = useApprovalActions(() => {
    setSelectedIds([]);
    setBatchNotes("");
  });

  if (approvalsQuery.isLoading) return <LoadingSkeleton rows={6} />;
  if (approvalsQuery.isError) {
    return <ErrorState title="Unable to load approvals" message={messageFromError(approvalsQuery.error)} retry={() => approvalsQuery.refetch()} />;
  }

  const approvals = (approvalsQuery.data ?? []).filter((approval) => matchesSearch(approval, search));
  const selectedApprovals = approvals.filter((approval) => selectedIds.includes(approval.id));
  const pendingCount = approvals.filter((item) => item.status === "pending").length;
  const awaitingExecutionCount = approvals.filter((item) => item.execution_status === "queued").length;
  const escalatedCount = approvals.filter((item) => item.status === "rejected" || item.execution_status === "failed").length;
  const avgQueueMinutes = approvals.length
    ? Math.round(
        approvals.reduce((total, approval) => total + Math.max(0, Date.now() - new Date(approval.created_at).getTime()), 0) /
          approvals.length /
          60000
      )
    : 0;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Approval Queue"
        description="Human reviewers validate AI-assisted actions, preserve auditability, and control what moves into execution."
        actions={
          <>
            <div className="relative w-full max-w-sm">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input className="pl-9" placeholder="Search queue, entity IDs, and notes" value={search} onChange={(event) => setSearch(event.target.value)} />
            </div>
            <Button variant="secondary">
              <Filter className="mr-2 h-4 w-4" />
              Filter
            </Button>
          </>
        }
      />

      <div className="dashboard-grid">
        <MetricCard label="Pending Approvals" value={pendingCount} hint="Items waiting on reviewer action" tone={pendingCount ? "warning" : "success"} />
        <MetricCard label="Avg Approval Time" value={`${avgQueueMinutes}m`} hint="Average queue age in the current result set" />
        <MetricCard label="Awaiting Execution" value={awaitingExecutionCount} hint="Approved items pending backend execution" tone={awaitingExecutionCount ? "warning" : "success"} />
        <MetricCard label="Escalated / Failed" value={escalatedCount} hint="Needs manager attention or retry" tone={escalatedCount ? "danger" : "success"} />
      </div>

      {!approvals.length ? (
        <EmptyState title="No approvals found" message="There are no approval items that match the current filter." />
      ) : (
        <div className="space-y-6">
          <SectionCard
            title="Reviewer workspace"
            actions={
              <Button variant="secondary" onClick={() => approvalsQuery.refetch()}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh queue
              </Button>
            }
          >
            <div className="space-y-3">
              {approvals.map((approval) => (
                <ApprovalQueueRow
                  key={approval.id}
                  approval={approval}
                  selected={selectedIds.includes(approval.id)}
                  onToggle={() =>
                    setSelectedIds((current) =>
                      current.includes(approval.id) ? current.filter((id) => id !== approval.id) : [...current, approval.id]
                    )
                  }
                />
              ))}
            </div>
          </SectionCard>

          {selectedApprovals.length ? (
            <Card className="sticky bottom-6 z-20 border-slate-950 bg-slate-950 p-4 text-white shadow-2xl">
              <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <StatusPill value={`${selectedApprovals.length} selected`} />
                    <p className="text-sm text-slate-300">Review actions apply only to the selected approval items.</p>
                  </div>
                  <Textarea
                    className="min-h-24 border-slate-700 bg-slate-900 text-slate-100 placeholder:text-slate-500 focus:border-accent-400 focus:ring-accent-500/20"
                    placeholder="Optional reviewer notes for the selected items"
                    value={batchNotes}
                    onChange={(event) => setBatchNotes(event.target.value)}
                  />
                </div>
                <div className="flex flex-wrap gap-3">
                  <Button variant="secondary" className="border-slate-700 bg-slate-900 text-white hover:bg-slate-800" onClick={() => setSelectedIds([])}>
                    Clear selection
                  </Button>
                  <Button
                    variant="secondary"
                    className="border-slate-700 bg-slate-900 text-white hover:bg-slate-800"
                    onClick={() =>
                      actionMutation.mutate({
                        action: "cancel",
                        approvalIds: selectedIds,
                        notes: batchNotes || notesFromAction("cancel", selectedIds.length)
                      })
                    }
                    disabled={actionMutation.isPending}
                  >
                    Escalate selected
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() =>
                      actionMutation.mutate({
                        action: "reject",
                        approvalIds: selectedIds,
                        notes: batchNotes || notesFromAction("reject", selectedIds.length)
                      })
                    }
                    disabled={actionMutation.isPending}
                  >
                    <XCircle className="mr-2 h-4 w-4" />
                    Reject selected
                  </Button>
                  <Button
                    onClick={() =>
                      actionMutation.mutate({
                        action: "approve",
                        approvalIds: selectedIds,
                        notes: batchNotes || notesFromAction("approve", selectedIds.length)
                      })
                    }
                    disabled={actionMutation.isPending}
                  >
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    Approve selected
                  </Button>
                </div>
              </div>
            </Card>
          ) : null}
        </div>
      )}

      {actionMutation.isError ? <ReviewRequiredBanner message={messageFromError(actionMutation.error)} /> : null}
    </div>
  );
}

function ApprovalDetailActions({
  approvalId,
  onDone
}: {
  approvalId: string;
  onDone: () => void;
}) {
  const [notes, setNotes] = React.useState("");
  const mutation = useApprovalActions(() => {
    setNotes("");
    onDone();
  });

  return (
    <div className="space-y-4">
      <Textarea placeholder="Reviewer notes" value={notes} onChange={(event) => setNotes(event.target.value)} />
      <div className="flex flex-wrap gap-3">
        <Button onClick={() => { mutation.mutate({ action: "approve", approvalIds: [approvalId], notes }); }} disabled={mutation.isPending}>
          Approve
        </Button>
        <Button variant="danger" onClick={() => { mutation.mutate({ action: "reject", approvalIds: [approvalId], notes }); }} disabled={mutation.isPending}>
          Reject
        </Button>
        <Button variant="secondary" onClick={() => { mutation.mutate({ action: "cancel", approvalIds: [approvalId], notes }); }} disabled={mutation.isPending}>
          Escalate / Cancel
        </Button>
        <Button variant="secondary" onClick={() => { mutation.mutate({ action: "retry", approvalIds: [approvalId], notes }); }} disabled={mutation.isPending}>
          Retry execution
        </Button>
      </div>
      {mutation.isError ? <p className="text-sm text-rose-700">{messageFromError(mutation.error)}</p> : null}
    </div>
  );
}

export function ApprovalDetailPage() {
  const { approvalId = "" } = useParams();
  const navigate = useNavigate();
  const approvalQuery = useApproval(approvalId);

  if (approvalQuery.isLoading) return <LoadingSkeleton rows={5} />;
  if (approvalQuery.isError || !approvalQuery.data) {
    return <ErrorState title="Unable to load approval" message={messageFromError(approvalQuery.error)} retry={() => approvalQuery.refetch()} />;
  }

  const approval = approvalQuery.data;

  return (
    <div className="space-y-8">
      <PageHeader
        title={titleize(approval.action_type)}
        description="Inspect reviewer context, reasoning, and execution state before taking a final action."
        actions={
          <Button variant="secondary" onClick={() => navigate("/app/approvals")}>
            Back to queue
          </Button>
        }
      />

      <div className="split-panel">
        <div className="space-y-6">
          <SectionCard title="Approval context">
            <KeyValueGrid
              items={[
                { label: "Entity type", value: titleize(approval.entity_type) },
                { label: "Entity ID", value: approval.entity_id },
                { label: "Approval status", value: <StatusPill value={approval.status} /> },
                { label: "Execution status", value: <StatusPill value={approval.execution_status ?? "not_started"} /> },
                { label: "Created", value: formatDate(approval.created_at) },
                { label: "Expires", value: formatDate(approval.expires_at) }
              ]}
            />
            <Card className="mt-5 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Reasoning</p>
              <p className="mt-3 text-sm leading-7 text-slate-700">{approval.reasoning}</p>
            </Card>
            {approval.review_notes ? (
              <Card className="mt-4 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Existing review notes</p>
                <p className="mt-3 text-sm leading-7 text-slate-700">{approval.review_notes}</p>
              </Card>
            ) : null}
          </SectionCard>
        </div>

        <div className="space-y-6">
          <DetailPanel title="Decision controls" subtitle="Use the supported backend actions only; execution stays separate from review.">
            <ApprovalDetailActions
              approvalId={approval.id}
              onDone={() => {
                approvalQuery.refetch();
              }}
            />
          </DetailPanel>

          <SectionCard title="Execution and follow-up">
            <div className="space-y-4 text-sm text-slate-700">
              <div className="flex items-center gap-2">
                <Clock3 className="h-4 w-4 text-slate-400" />
                <p>Execution status: <span className="font-medium text-slate-900">{titleize(approval.execution_status ?? "not_started")}</span></p>
              </div>
              {approval.execution_error ? (
                <Card className="border-rose-200 bg-rose-50 p-4 text-rose-800">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="mt-0.5 h-4 w-4" />
                    <div>
                      <p className="font-medium text-rose-900">Execution error</p>
                      <p className="mt-1">{approval.execution_error}</p>
                    </div>
                  </div>
                </Card>
              ) : (
                <p>The reviewer flow controls approval intent. Backend execution remains an auditable downstream step.</p>
              )}
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
