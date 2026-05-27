import * as React from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowUpRight,
  CheckCircle2,
  CircleAlert,
  Clock3,
  Link2,
  RefreshCw,
  Store as StoreIcon,
  Workflow
} from "lucide-react";

import { storesApi } from "@frontend/api-client";
import { Button, Card, Input } from "@frontend/ui";

import { useAuth } from "@/app/use-auth";
import { useAppState } from "@/app/use-app-state";
import {
  ActivityTimeline,
  DetailPanel,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
  MetricCard,
  PageHeader,
  SectionCard,
  StatusPill
} from "@/components/common";
import { formatDate, titleize } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function DashboardNavCard({
  title,
  description,
  href,
  count,
  tone = "neutral"
}: {
  title: string;
  description: string;
  href: string;
  count?: number;
  tone?: "neutral" | "warning" | "danger" | "success";
}) {
  const toneClasses = {
    neutral: "border-slate-200 bg-white",
    warning: "border-amber-200 bg-amber-50/70",
    danger: "border-rose-200 bg-rose-50/70",
    success: "border-emerald-200 bg-emerald-50/70"
  };

  return (
    <Link to={href} className="block">
      <Card className={`h-full p-5 transition hover:-translate-y-0.5 hover:shadow-md ${toneClasses[tone]}`}>
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            <p className="font-semibold text-slate-950">{title}</p>
            <p className="text-sm leading-6 text-slate-600">{description}</p>
          </div>
          <ArrowUpRight className="h-4 w-4 text-slate-400" />
        </div>
        {typeof count === "number" ? <p className="mt-4 text-2xl font-semibold text-slate-950">{count}</p> : null}
      </Card>
    </Link>
  );
}

export function DashboardPage() {
  const { me } = useAuth();
  const { selectedStoreId } = useAppState();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const summaryQuery = useQuery({
    queryKey: ["dashboard", selectedStoreId],
    queryFn: () => storesApi.getDashboardSummary(selectedStoreId!),
    enabled: Boolean(selectedStoreId)
  });

  const syncMutation = useMutation({
    mutationFn: () => storesApi.createSyncRun(selectedStoreId!, "manual_full"),
    onSuccess: () => {
      if (selectedStoreId) {
        queryClient.invalidateQueries({ queryKey: ["dashboard", selectedStoreId] });
        queryClient.invalidateQueries({ queryKey: ["stores", "sync-runs", selectedStoreId] });
        navigate(`/app/stores/${selectedStoreId}/sync-runs`);
      }
    }
  });

  if (!selectedStoreId) {
    return (
      <EmptyState
        title="No accessible store selected"
        message="Choose a connected store to open the operations dashboard."
        action={
          <Link to="/app/stores">
            <Button>Open stores</Button>
          </Link>
        }
      />
    );
  }

  if (summaryQuery.isLoading) return <LoadingSkeleton rows={6} />;
  if (summaryQuery.isError) {
    return <ErrorState title="Could not load dashboard" message={messageFromError(summaryQuery.error)} retry={() => summaryQuery.refetch()} />;
  }

  const summary = summaryQuery.data!;
  const store = me?.accessible_stores.find((entry) => entry.id === selectedStoreId) ?? null;

  const activityItems = [
    {
      title: "Latest sync state",
      description: summary.latest_sync_status
        ? `${titleize(summary.latest_sync_status)}${summary.latest_sync_completed_at ? ` at ${formatDate(summary.latest_sync_completed_at)}` : ""}`
        : "No successful sync recorded yet.",
      created_at: summary.latest_sync_completed_at ?? new Date().toISOString()
    },
    {
      title: "Recent agent runs",
      description: `${summary.recent_agent_runs} AI-assisted runs recorded in the recent window.`,
      created_at: new Date().toISOString()
    },
    {
      title: "Workflow failures",
      description: `${summary.recent_workflow_failures} recent failures need follow-up.`,
      created_at: new Date().toISOString()
    }
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Operations Overview"
        description={`Real-time coordination surface for ${store?.name ?? "the selected store"} with AI-assisted workflows and human-controlled execution.`}
        actions={
          <>
            <Link to="/app/approvals">
              <Button variant="secondary">Review Approvals</Button>
            </Link>
            <Button onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending}>
              {syncMutation.isPending ? "Running sync..." : "Run Sync"}
            </Button>
          </>
        }
      />

      <div className="dashboard-grid">
        <MetricCard label="Sync Health" value={summary.latest_sync_status ? titleize(summary.latest_sync_status) : "Unknown"} hint={summary.latest_sync_completed_at ? `Last completed ${formatDate(summary.latest_sync_completed_at)}` : "Run a sync to populate the store."} tone={summary.latest_sync_status === "succeeded" ? "success" : "warning"} />
        <MetricCard label="Pending Approvals" value={summary.pending_approval_count} hint="Items waiting on reviewer action" tone={summary.pending_approval_count > 0 ? "warning" : "neutral"} />
        <MetricCard label="Fraud / Workflow Alerts" value={summary.recent_workflow_failures} hint="Recent failed or blocked workflow paths" tone={summary.recent_workflow_failures > 0 ? "danger" : "success"} />
        <MetricCard label="Low Stock Alerts" value={summary.low_inventory_count} hint="Inventory items below threshold" tone={summary.low_inventory_count > 0 ? "warning" : "success"} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <SectionCard title="AI drafts and review-required work">
          <div className="grid gap-4 md:grid-cols-2">
            <DashboardNavCard
              title="Catalog drafts"
              description="Generate, edit, and submit product content drafts for approval."
              href={`/app/catalog/${selectedStoreId}/products`}
              count={summary.product_count}
            />
            <DashboardNavCard
              title="Support workspace"
              description="Open grounded reply drafts and operator review queues."
              href={`/app/support/${selectedStoreId}/conversations`}
              count={summary.customer_count}
              tone="neutral"
            />
            <DashboardNavCard
              title="Fraud review"
              description="Inspect high-risk orders and record internal decisions."
              href={`/app/fraud/${selectedStoreId}/reviews`}
              count={summary.recent_workflow_failures}
              tone={summary.recent_workflow_failures > 0 ? "danger" : "neutral"}
            />
            <DashboardNavCard
              title="Inventory follow-up"
              description="Review low-stock alerts and supplier drafts."
              href={`/app/inventory/${selectedStoreId}`}
              count={summary.low_inventory_count}
              tone={summary.low_inventory_count > 0 ? "warning" : "success"}
            />
          </div>
        </SectionCard>

        <SectionCard title="Recent activity">
          <ActivityTimeline items={activityItems} />
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SectionCard title="Store health snapshot">
          <KeyValueGrid
            items={[
              { label: "Store", value: store?.name ?? "Selected store" },
              { label: "Domain", value: store?.domain ?? "Unknown" },
              { label: "Connection", value: <StatusPill value={store?.connection_status ?? "unknown"} /> },
              { label: "Products", value: summary.product_count },
              { label: "Orders", value: summary.order_count },
              { label: "Customers", value: summary.customer_count }
            ]}
          />
        </SectionCard>

        <SectionCard title="Next best pages">
          <div className="grid gap-3 md:grid-cols-2">
            <Link to={`/app/stores/${selectedStoreId}`} className="rounded-2xl border border-slate-200 p-4 transition hover:border-accent-300 hover:bg-accent-50">
              <div className="flex items-center gap-3">
                <StoreIcon className="h-5 w-5 text-accent-600" />
                <div>
                  <p className="font-medium text-slate-950">Store detail</p>
                  <p className="text-sm text-slate-600">Connection health and metadata</p>
                </div>
              </div>
            </Link>
            <Link to={`/app/stores/${selectedStoreId}/sync-runs`} className="rounded-2xl border border-slate-200 p-4 transition hover:border-accent-300 hover:bg-accent-50">
              <div className="flex items-center gap-3">
                <Workflow className="h-5 w-5 text-accent-600" />
                <div>
                  <p className="font-medium text-slate-950">Sync runs</p>
                  <p className="text-sm text-slate-600">Queue, retry, and run history</p>
                </div>
              </div>
            </Link>
            <Link to={`/app/analytics/${selectedStoreId}`} className="rounded-2xl border border-slate-200 p-4 transition hover:border-accent-300 hover:bg-accent-50">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                <div>
                  <p className="font-medium text-slate-950">Analytics</p>
                  <p className="text-sm text-slate-600">Operational and automation metrics</p>
                </div>
              </div>
            </Link>
            <Link to={`/app/runtime/workflows/${selectedStoreId}`} className="rounded-2xl border border-slate-200 p-4 transition hover:border-accent-300 hover:bg-accent-50">
              <div className="flex items-center gap-3">
                <RefreshCw className="h-5 w-5 text-accent-600" />
                <div>
                  <p className="font-medium text-slate-950">Runtime history</p>
                  <p className="text-sm text-slate-600">Workflow, agent, and audit traces</p>
                </div>
              </div>
            </Link>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

export function StoreListPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { me } = useAuth();
  const { selectedStoreId, setSelectedStoreId } = useAppState();
  const [form, setForm] = React.useState({
    name: "",
    domain: "",
    currency: "USD",
    timezone: "UTC"
  });

  const storesQuery = useQuery({
    queryKey: ["stores"],
    queryFn: () => storesApi.list()
  });

  const createStore = useMutation({
    mutationFn: () =>
      storesApi.create({
        name: form.name,
        domain: form.domain,
        currency: form.currency,
        timezone: form.timezone
      }),
    onSuccess: (store) => {
      queryClient.invalidateQueries({ queryKey: ["stores"] });
      queryClient.invalidateQueries({ queryKey: ["auth-me"] });
      setSelectedStoreId(store.id);
      navigate(`/app/stores/${store.id}`);
      setForm({ name: "", domain: "", currency: "USD", timezone: "UTC" });
    }
  });

  const stores = storesQuery.data ?? me?.accessible_stores ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Stores"
        description="Manage connected commerce stores, choose the active workspace context, and bootstrap new integrations."
      />

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <SectionCard title="Connected stores">
          {storesQuery.isLoading ? (
            <LoadingSkeleton rows={5} />
          ) : storesQuery.isError ? (
            <ErrorState title="Could not load stores" message={messageFromError(storesQuery.error)} retry={() => storesQuery.refetch()} />
          ) : stores.length === 0 ? (
            <EmptyState title="No stores yet" message="Create your first store to connect Shopify and start the operator workflows." />
          ) : (
            <div className="space-y-3">
              {stores.map((store: typeof stores[number]) => {
                const isSelected = selectedStoreId === store.id;
                return (
                  <Card key={store.id} className={`p-5 ${isSelected ? "border-accent-300 bg-accent-50/70" : ""}`}>
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-slate-950">{store.name}</p>
                          <StatusPill value={store.connection_status} />
                        </div>
                        <p className="text-sm text-slate-600">{store.domain}</p>
                        <p className="text-xs text-slate-500">
                          {store.currency ?? "USD"} · {store.timezone ?? "UTC"} · Last sync {store.last_successful_sync_at ? formatDate(store.last_successful_sync_at) : "not completed"}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-3">
                        {!isSelected ? (
                          <Button variant="secondary" onClick={() => setSelectedStoreId(store.id)}>
                            Use store
                          </Button>
                        ) : null}
                        <Link to={`/app/stores/${store.id}`}>
                          <Button>Open detail</Button>
                        </Link>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </SectionCard>

        <SectionCard title="Create store">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              createStore.mutate();
            }}
          >
            <Input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} placeholder="Store name" />
            <Input value={form.domain} onChange={(event) => setForm((current) => ({ ...current, domain: event.target.value }))} placeholder="my-store.myshopify.com" />
            <div className="grid gap-4 sm:grid-cols-2">
              <Input value={form.currency} onChange={(event) => setForm((current) => ({ ...current, currency: event.target.value }))} placeholder="USD" />
              <Input value={form.timezone} onChange={(event) => setForm((current) => ({ ...current, timezone: event.target.value }))} placeholder="UTC" />
            </div>
            <Button className="w-full" disabled={createStore.isPending} type="submit">
              {createStore.isPending ? "Creating..." : "Create store"}
            </Button>
            {createStore.isError ? <p className="text-sm text-rose-700">{messageFromError(createStore.error)}</p> : null}
          </form>
        </SectionCard>
      </div>
    </div>
  );
}

export function StoreDetailPage() {
  const { storeId = "" } = useParams();
  const { setSelectedStoreId } = useAppState();

  const storeQuery = useQuery({
    queryKey: ["store", storeId],
    queryFn: () => storesApi.get(storeId),
    enabled: Boolean(storeId)
  });

  React.useEffect(() => {
    if (storeId) setSelectedStoreId(storeId);
  }, [setSelectedStoreId, storeId]);

  if (storeQuery.isLoading) return <LoadingSkeleton rows={4} />;
  if (storeQuery.isError) {
    return <ErrorState title="Could not load store detail" message={messageFromError(storeQuery.error)} retry={() => storeQuery.refetch()} />;
  }

  const store = storeQuery.data!;

  return (
    <div className="space-y-8">
      <PageHeader
        title={store.name}
        description="Store-level integration, sync, and operational metadata."
        actions={
          <>
            <Link to={`/app/stores/${store.id}/integration`}>
              <Button variant="secondary">Integration</Button>
            </Link>
            <Link to={`/app/stores/${store.id}/sync-runs`}>
              <Button>Sync runs</Button>
            </Link>
          </>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SectionCard title="Store profile">
          <KeyValueGrid
            items={[
              { label: "Platform", value: titleize(store.platform) },
              { label: "Domain", value: store.domain },
              { label: "Connection", value: <StatusPill value={store.connection_status} /> },
              { label: "Currency", value: store.currency ?? "USD" },
              { label: "Timezone", value: store.timezone ?? "UTC" },
              { label: "Created", value: formatDate(store.created_at) }
            ]}
          />
        </SectionCard>

        <SectionCard title="Recommended next steps">
          <div className="space-y-3">
            <Card className="p-4">
              <div className="flex items-start gap-3">
                <Link2 className="mt-0.5 h-5 w-5 text-accent-600" />
                <div>
                  <p className="font-medium text-slate-950">Complete or verify Shopify connection</p>
                  <p className="mt-1 text-sm text-slate-600">Open integration to review scope access and generate a fresh install URL if needed.</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-start gap-3">
                <RefreshCw className="mt-0.5 h-5 w-5 text-accent-600" />
                <div>
                  <p className="font-medium text-slate-950">Run a sync</p>
                  <p className="mt-1 text-sm text-slate-600">Populate products, orders, and customers before using catalog, support, fraud, and inventory workspaces.</p>
                </div>
              </div>
            </Card>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

export function StoreIntegrationPage() {
  const { storeId = "" } = useParams();

  const integrationQuery = useQuery({
    queryKey: ["store", "integration", storeId],
    queryFn: () => storesApi.getIntegration(storeId),
    enabled: Boolean(storeId)
  });

  const installUrlMutation = useMutation({
    mutationFn: () => storesApi.createInstallUrl(storeId, `${window.location.origin}/shopify/callback`)
  });

  if (integrationQuery.isLoading) return <LoadingSkeleton rows={4} />;
  if (integrationQuery.isError) {
    return <ErrorState title="Could not load integration state" message={messageFromError(integrationQuery.error)} retry={() => integrationQuery.refetch()} />;
  }

  const integration = integrationQuery.data!;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Shopify integration"
        description="Review connection health, scope coverage, and generate the install URL used to connect or reconnect this store."
        actions={
          <Button onClick={() => installUrlMutation.mutate()} disabled={installUrlMutation.isPending}>
            {installUrlMutation.isPending ? "Preparing..." : "Generate Install URL"}
          </Button>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <DetailPanel title="Connection state" subtitle="Current provider link and sync readiness">
          <KeyValueGrid
            items={[
              { label: "Provider", value: titleize(integration.provider) },
              { label: "Status", value: <StatusPill value={integration.status} /> },
              { label: "Last successful sync", value: integration.last_successful_sync_at ? formatDate(integration.last_successful_sync_at) : "Not synced yet" }
            ]}
          />
        </DetailPanel>

        <SectionCard title="Granted scopes">
          {integration.scopes.length ? (
            <div className="flex flex-wrap gap-2">
              {integration.scopes.map((scope) => (
                <StatusPill key={scope} value={scope} />
              ))}
            </div>
          ) : (
            <EmptyState title="No scopes reported yet" message="Generate and complete the install flow to connect Shopify scopes." />
          )}

          {installUrlMutation.data ? (
            <Card className="mt-5 border-accent-200 bg-accent-50 p-4">
              <p className="font-medium text-accent-700">Install URL ready</p>
              <p className="mt-2 break-all text-sm text-accent-700">{installUrlMutation.data.install_url}</p>
              <div className="mt-4 flex flex-wrap gap-3">
                <Button variant="secondary" onClick={() => navigator.clipboard.writeText(installUrlMutation.data.install_url)}>
                  Copy URL
                </Button>
                <a href={installUrlMutation.data.install_url} target="_blank" rel="noreferrer">
                  <Button>Open install flow</Button>
                </a>
              </div>
            </Card>
          ) : null}
        </SectionCard>
      </div>
    </div>
  );
}

export function StoreSyncRunsPage() {
  const { storeId = "" } = useParams();
  const queryClient = useQueryClient();
  const [selectedRunId, setSelectedRunId] = React.useState<string | null>(null);

  const runsQuery = useQuery({
    queryKey: ["stores", "sync-runs", storeId],
    queryFn: () => storesApi.listSyncRuns(storeId),
    enabled: Boolean(storeId)
  });

  const selectedRunQuery = useQuery({
    queryKey: ["stores", "sync-run", storeId, selectedRunId],
    queryFn: () => storesApi.getSyncRun(storeId, selectedRunId!),
    enabled: Boolean(storeId && selectedRunId)
  });

  const triggerRun = useMutation({
    mutationFn: () => storesApi.createSyncRun(storeId, "manual_full"),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: ["stores", "sync-runs", storeId] });
      setSelectedRunId(run.id);
    }
  });

  const retryRun = useMutation({
    mutationFn: (syncRunId: string) => storesApi.retrySyncRun(storeId, syncRunId),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: ["stores", "sync-runs", storeId] });
      setSelectedRunId(run.id);
    }
  });

  const runs = runsQuery.data ?? [];
  const selectedRun = selectedRunQuery.data ?? runs.find((run) => run.id === selectedRunId) ?? runs[0] ?? null;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Sync runs"
        description="Queue manual syncs, monitor import outcomes, and retry failed runs without leaving the store workspace."
        actions={
          <Button onClick={() => triggerRun.mutate()} disabled={triggerRun.isPending}>
            {triggerRun.isPending ? "Queueing..." : "Run Sync"}
          </Button>
        }
      />

      {runsQuery.isLoading ? (
        <LoadingSkeleton rows={6} />
      ) : runsQuery.isError ? (
        <ErrorState title="Could not load sync runs" message={messageFromError(runsQuery.error)} retry={() => runsQuery.refetch()} />
      ) : runs.length === 0 ? (
        <EmptyState title="No sync runs yet" message="Queue a manual sync to start importing store data." action={<Button onClick={() => triggerRun.mutate()}>Run Sync</Button>} />
      ) : (
        <div className="workspace-grid">
          <SectionCard title="Run history">
            <div className="space-y-3">
              {runs.map((run) => (
                <button
                  key={run.id}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    selectedRun?.id === run.id ? "border-accent-300 bg-accent-50" : "border-slate-200 bg-white hover:border-accent-200"
                  }`}
                  onClick={() => setSelectedRunId(run.id)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-slate-950">{titleize(run.mode)}</p>
                        <StatusPill value={run.status} />
                      </div>
                      <p className="text-sm text-slate-600">
                        Imported {run.records_imported} records · Failed {run.records_failed}
                      </p>
                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                        <span className="inline-flex items-center gap-1"><Clock3 className="h-3.5 w-3.5" /> {formatDate(run.created_at)}</span>
                        {run.retry_of_sync_run_id ? <span>Retry of {run.retry_of_sync_run_id}</span> : null}
                      </div>
                    </div>
                    {(run.status === "failed" || run.records_failed > 0) ? (
                      <Button
                        variant="secondary"
                        onClick={(event) => {
                          event.stopPropagation();
                          retryRun.mutate(run.id);
                        }}
                        disabled={retryRun.isPending}
                      >
                        Retry
                      </Button>
                    ) : null}
                  </div>
                </button>
              ))}
            </div>
          </SectionCard>

          {selectedRun ? (
            <div className="space-y-6">
              <DetailPanel title="Selected sync run" subtitle="Inspect the selected run and its import counts.">
                <KeyValueGrid
                  items={[
                    { label: "Status", value: <StatusPill value={selectedRun.status} /> },
                    { label: "Mode", value: titleize(selectedRun.mode) },
                    { label: "Started", value: selectedRun.started_at ? formatDate(selectedRun.started_at) : "Pending" },
                    { label: "Completed", value: selectedRun.completed_at ? formatDate(selectedRun.completed_at) : "Not completed" },
                    { label: "Imported", value: selectedRun.records_imported },
                    { label: "Failed", value: selectedRun.records_failed }
                  ]}
                />
              </DetailPanel>

              <SectionCard title="Entity counts">
                {Object.keys(selectedRun.entity_counts_json).length ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {Object.entries(selectedRun.entity_counts_json).map(([entity, count]) => (
                      <Card key={entity} className="p-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{entity}</p>
                        <p className="mt-2 text-2xl font-semibold text-slate-950">{String(count)}</p>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <EmptyState title="No entity counts reported" message="This run has not produced entity counts yet." />
                )}
              </SectionCard>

              {selectedRun.error_summary ? (
                <Card className="border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                  <div className="flex items-start gap-3">
                    <CircleAlert className="mt-0.5 h-4 w-4" />
                    <div>
                      <p className="font-medium text-rose-900">Error summary</p>
                      <p className="mt-1">{selectedRun.error_summary}</p>
                    </div>
                  </div>
                </Card>
              ) : null}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
