import * as React from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Clock3, Filter, RefreshCw, Search, Sparkles, XCircle } from "lucide-react";

import { approvalsApi } from "@frontend/api-client";
import { Button, Card, Checkbox, Input, Textarea } from "@frontend/ui";
import { useApproval, useApprovalActions, useApprovals } from "@/hooks/use-approvals";

import {
  DetailPanel,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
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

function formatApprovalEntityLabel(approval: Awaited<ReturnType<typeof approvalsApi.list>>[number] | Awaited<ReturnType<typeof approvalsApi.get>>) {
  return titleize(approval.entity_type.replaceAll("_", " "));
}

function matchesSearch(approval: Awaited<ReturnType<typeof approvalsApi.list>>[number], query: string) {
  if (!query) return true;
  const haystack = [approval.action_type, approval.entity_type, approval.entity_id, approval.reasoning, approval.review_notes ?? "", approval.status, approval.execution_status ?? ""]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query.toLowerCase());
}

function ApprovalMetricStrip({
  label,
  value,
  hint,
  tone = "neutral"
}: {
  label: string;
  value: string | number;
  hint: string;
  tone?: "neutral" | "warning" | "danger" | "success";
}) {
  const toneClasses = {
    neutral: "border-slate-200 bg-white",
    warning: "border-amber-200 bg-[linear-gradient(135deg,rgba(254,243,199,0.55),white)]",
    danger: "border-rose-200 bg-[linear-gradient(135deg,rgba(255,228,230,0.55),white)]",
    success: "border-emerald-200 bg-[linear-gradient(135deg,rgba(209,250,229,0.55),white)]"
  };

  return (
    <div className={`rounded-[1.3rem] border px-4 py-4 ${toneClasses[tone]}`}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{hint}</p>
    </div>
  );
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
      className={`block cursor-pointer rounded-[1.35rem] border px-4 py-4 transition ${
        selected ? "border-accent-300 bg-accent-50" : "border-slate-200 bg-white hover:border-accent-200 hover:bg-slate-50"
      }`}
    >
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_0.82fr_auto]">
        <div className="min-w-0 space-y-4">
          <div className="flex items-start gap-3">
            <Checkbox checked={selected} onChange={onToggle} />
            <div className="min-w-0 pt-0.5">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-semibold text-slate-950">{titleize(approval.action_type)}</p>
                <StatusPill value={approval.status} />
              </div>
              <p className="mt-2 text-sm text-slate-600">{formatApprovalEntityLabel(approval)}</p>
            </div>
          </div>
          <div className="rounded-[1.1rem] border border-slate-200 bg-slate-50/80 px-4 py-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Context / details</p>
            <p className="mt-2 text-sm leading-6 text-slate-700">{approval.reasoning}</p>
          </div>
        </div>

        <div className="grid gap-3 text-sm text-slate-600 sm:grid-cols-2 xl:grid-cols-1">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Execution</p>
            <div className="mt-2">
              <StatusPill value={approval.execution_status ?? "not_started"} />
            </div>
            {approval.execution_error ? <p className="mt-2 text-xs leading-5 text-rose-700">{approval.execution_error}</p> : null}
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Created</p>
            <p className="mt-2 text-sm text-slate-700">{formatDate(approval.created_at)}</p>
            <p className="mt-1 text-xs text-slate-500">Expires {formatDate(approval.expires_at)}</p>
          </div>
        </div>

        <div className="flex flex-col items-start gap-2 text-sm xl:items-end xl:text-right">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Open detail</p>
          <Link className="font-medium text-accent-600 hover:text-accent-700" to={`/app/approvals/${approval.id}`}>
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
              <Input className="pl-9" placeholder="Search queue, approval context, and notes" value={search} onChange={(event) => setSearch(event.target.value)} />
            </div>
            <Button variant="secondary">
              <Filter className="mr-2 h-4 w-4" />
              Filter
            </Button>
          </>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(21rem,0.92fr)]">
        <SectionCard title="Reviewer workspace">
          <div className="space-y-4">
            <div className="rounded-[1.35rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(248,250,252,0.98),rgba(239,246,255,0.82))] px-5 py-4">
              <p className="text-sm font-semibold text-slate-950">Human review controls the final intent</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Review AI-assisted actions with reasoning, audit notes, and execution context before anything moves downstream.
              </p>
            </div>

            {!approvals.length ? (
              <EmptyState title="No approvals found" message="There are no approval items that match the current filter." />
            ) : (
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
            )}
          </div>
        </SectionCard>

        <div className="space-y-6">
          <div className="surface-panel p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Queue signals</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Monitor review load, execution lag, and failures that still need human handling.
                </p>
              </div>
              <Button variant="secondary" onClick={() => approvalsQuery.refetch()}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh queue
              </Button>
            </div>

            <div className="mt-5 space-y-3">
              <ApprovalMetricStrip
                label="Pending approvals"
                value={pendingCount}
                hint="Items waiting on reviewer action"
                tone={pendingCount ? "warning" : "success"}
              />
              <ApprovalMetricStrip
                label="Avg approval time"
                value={`${avgQueueMinutes}m`}
                hint="Average queue age in the current result set"
              />
              <ApprovalMetricStrip
                label="Awaiting execution"
                value={awaitingExecutionCount}
                hint="Approved items pending backend execution"
                tone={awaitingExecutionCount ? "warning" : "success"}
              />
              <ApprovalMetricStrip
                label="Escalated / failed"
                value={escalatedCount}
                hint="Needs manager attention or retry"
                tone={escalatedCount ? "danger" : "success"}
              />
            </div>
          </div>

          {selectedApprovals.length ? (
            <Card className="sticky bottom-6 z-20 overflow-hidden border border-slate-200 bg-white/95 shadow-[0_22px_60px_rgba(15,23,42,0.16)] backdrop-blur">
              <div className="border-b border-slate-200 bg-[linear-gradient(135deg,rgba(239,246,255,0.95),rgba(255,255,255,0.98))] px-5 py-4">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-3">
                      <StatusPill value={`${selectedApprovals.length} selected`} />
                      <div className="inline-flex items-center gap-2 rounded-full bg-accent-50 px-3 py-1 text-xs font-semibold text-accent-700">
                        <Sparkles className="h-3.5 w-3.5" />
                        Reviewer actions
                      </div>
                    </div>
                    <p className="text-sm text-slate-600">Review actions apply only to the selected approval items. Add notes if you want them preserved in the audit trail.</p>
                  </div>
                  <div className="max-w-xl text-sm text-slate-500">
                    {selectedApprovals.map((approval) => `${titleize(approval.action_type)} / ${formatApprovalEntityLabel(approval)}`).slice(0, 2).join(" / ")}
                    {selectedApprovals.length > 2 ? ` +${selectedApprovals.length - 2} more` : ""}
                  </div>
                </div>
              </div>

              <div className="grid gap-5 px-5 py-5 xl:grid-cols-[minmax(0,1.1fr)_auto] xl:items-end">
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Reviewer notes</p>
                  <Textarea
                    className="min-h-28 border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 focus:border-accent-400 focus:ring-accent-100"
                    placeholder="Optional reviewer notes for the selected items"
                    value={batchNotes}
                    onChange={(event) => setBatchNotes(event.target.value)}
                  />
                </div>

                <div className="space-y-2 xl:min-w-[22rem]">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Actions</p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Button
                      variant="secondary"
                      className="h-11 border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                      onClick={() => setSelectedIds([])}
                    >
                      Clear selection
                    </Button>
                    <Button
                      variant="secondary"
                      className="h-11 border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100"
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
                      className="h-11"
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
                      className="h-11"
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
              </div>
            </Card>
          ) : null}
        </div>
      </div>

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

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(22rem,0.95fr)]">
        <div className="space-y-6">
          <SectionCard title="Approval context">
            <div className="space-y-5">
              <div className="rounded-[1.35rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(248,250,252,0.98),rgba(239,246,255,0.82))] px-5 py-4">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusPill value={approval.status} />
                      <StatusPill value={approval.execution_status ?? "not_started"} />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-950">{formatApprovalEntityLabel(approval)}</p>
                      <p className="mt-1 text-sm leading-6 text-slate-600">Created {formatDate(approval.created_at)} and expires {formatDate(approval.expires_at)}.</p>
                    </div>
                  </div>
                </div>
              </div>

              <KeyValueGrid
                items={[
                  { label: "Entity", value: formatApprovalEntityLabel(approval) },
                  { label: "Approval status", value: <StatusPill value={approval.status} /> },
                  { label: "Execution status", value: <StatusPill value={approval.execution_status ?? "not_started"} /> },
                  { label: "Created", value: formatDate(approval.created_at) },
                  { label: "Expires", value: formatDate(approval.expires_at) }
                ]}
              />

              <Card className="p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Reasoning</p>
                <p className="mt-3 text-sm leading-7 text-slate-700">{approval.reasoning}</p>
              </Card>
            </div>

            {approval.review_notes ? (
              <Card className="mt-4 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Existing review notes</p>
                <p className="mt-3 text-sm leading-7 text-slate-700">{approval.review_notes}</p>
              </Card>
            ) : null}
          </SectionCard>
        </div>

        <div className="space-y-6 xl:sticky xl:top-24 xl:self-start">
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
              <div className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-4">
                <div className="flex items-center gap-2">
                  <Clock3 className="h-4 w-4 text-slate-400" />
                  <p>
                    Execution status: <span className="font-medium text-slate-900">{titleize(approval.execution_status ?? "not_started")}</span>
                  </p>
                </div>
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
