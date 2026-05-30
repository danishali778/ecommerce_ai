import * as React from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowUpRight,
  Boxes,
  CheckCircle2,
  CircleAlert,
  Clock3,
  Link2,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Store as StoreIcon,
  Workflow,
  Wrench
} from "lucide-react";
import { Button, Card, Input } from "@frontend/ui";

import { useAuth } from "@/hooks/use-auth";
import { useAppState } from "@/hooks/use-app-state";
import {
  useCreateStore,
  useCreateStoreInstallUrl,
  useDashboardSummary,
  useRunDashboardSync,
  useStore,
  useStoreIntegration,
  useStoresList,
  useStoreSyncRun,
  useStoreSyncRuns,
  useTriggerStoreSync,
  useRetryStoreSyncRun
} from "@/hooks/use-stores";
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
  tone = "neutral",
  icon: Icon
}: {
  title: string;
  description: string;
  href: string;
  count?: number;
  tone?: "neutral" | "warning" | "danger" | "success";
  icon: React.ComponentType<{ className?: string }>;
}) {
  const toneClasses = {
    neutral: "border-slate-200 bg-white",
    warning: "border-amber-200 bg-[linear-gradient(135deg,rgba(254,243,199,0.45),white)]",
    danger: "border-rose-200 bg-[linear-gradient(135deg,rgba(255,228,230,0.45),white)]",
    success: "border-emerald-200 bg-[linear-gradient(135deg,rgba(209,250,229,0.45),white)]"
  };

  return (
    <Link to={href} className="block">
      <Card className={`rounded-[1.35rem] p-4 transition hover:-translate-y-0.5 hover:shadow-lg ${toneClasses[tone]}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3">
            <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/90 bg-white/90 shadow-sm">
              <Icon className="h-4 w-4 text-accent-600" />
            </span>
            <div className="min-w-0 space-y-1.5">
              <p className="font-semibold text-slate-950">{title}</p>
              <p className="text-sm leading-6 text-slate-600">{description}</p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            {typeof count === "number" ? <p className="text-2xl font-semibold tracking-tight text-slate-950">{count}</p> : null}
            <ArrowUpRight className="h-4 w-4 text-slate-400" />
          </div>
        </div>
      </Card>
    </Link>
  );
}

function DashboardMetricBand({
  label,
  value,
  detail,
  tone = "neutral"
}: {
  label: string;
  value: string | number;
  detail: string;
  tone?: "neutral" | "info" | "success" | "warning" | "danger";
}) {
  const toneClasses = {
    neutral: "border-slate-200 bg-white",
    info: "border-sky-200 bg-[linear-gradient(135deg,rgba(224,242,254,0.65),white)]",
    success: "border-emerald-200 bg-[linear-gradient(135deg,rgba(209,250,229,0.65),white)]",
    warning: "border-amber-200 bg-[linear-gradient(135deg,rgba(254,243,199,0.65),white)]",
    danger: "border-rose-200 bg-[linear-gradient(135deg,rgba(255,228,230,0.65),white)]"
  };

  return (
    <div className={`rounded-[1.3rem] border px-4 py-4 ${toneClasses[tone]}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</p>
          <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
        </div>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">{detail}</p>
    </div>
  );
}

export function DashboardPage() {
  const { me } = useAuth();
  const { selectedStoreId } = useAppState();
  const navigate = useNavigate();
  const summaryQuery = useDashboardSummary(selectedStoreId);
  const syncMutation = useRunDashboardSync(selectedStoreId, () => {
    if (selectedStoreId) {
      navigate(`/app/stores/${selectedStoreId}/sync-runs`);
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

  const workspaceHighlights = [
    {
      label: "Recent AI runs",
      value: summary.recent_agent_runs,
      copy: "AI-assisted workflows completed in the recent window.",
      icon: Sparkles
    },
    {
      label: "Connected domain",
      value: store?.domain ?? "Unknown",
      copy: "Active commerce surface for search, sync, and approvals.",
      icon: StoreIcon
    },
    {
      label: "Workflow risk",
      value: summary.recent_workflow_failures,
      copy: "Recent failures or blocked paths needing human attention.",
      icon: ShieldAlert
    }
  ];

  const dashboardSignals = [
    {
      label: "Sync health",
      value: summary.latest_sync_status ? titleize(summary.latest_sync_status) : "Unknown",
      detail: summary.latest_sync_completed_at ? `Last completed ${formatDate(summary.latest_sync_completed_at)}` : "Run a sync to populate the store.",
      tone: summary.latest_sync_status === "succeeded" ? "success" : "warning"
    },
    {
      label: "Pending approvals",
      value: summary.pending_approval_count,
      detail: "Items waiting on reviewer action before any customer-facing or operational execution.",
      tone: summary.pending_approval_count > 0 ? "warning" : "neutral"
    },
    {
      label: "Workflow alerts",
      value: summary.recent_workflow_failures,
      detail: "Recent failed or blocked workflow paths that still need a human checkpoint.",
      tone: summary.recent_workflow_failures > 0 ? "danger" : "success"
    },
    {
      label: "Low-stock alerts",
      value: summary.low_inventory_count,
      detail: "Inventory items below threshold that may need reorder review or supplier follow-up.",
      tone: summary.low_inventory_count > 0 ? "warning" : "success"
    }
  ] as const;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Operations Overview"
        description={`Real-time coordination surface for ${store?.name ?? "the selected store"} with AI-assisted workflows and human-controlled execution.`}
        actions={
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:justify-end">
            <Link to="/app/approvals">
              <Button variant="secondary" className="h-11 w-full rounded-xl px-5 text-sm font-semibold shadow-sm sm:w-auto">
                Review Approvals
              </Button>
            </Link>
            <Button className="h-11 w-full rounded-xl px-5 text-sm font-semibold shadow-sm sm:w-auto" onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending}>
              {syncMutation.isPending ? "Running sync..." : "Run Sync"}
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1.12fr_0.88fr]">
        <Card className="overflow-hidden rounded-[2rem] border-accent-200 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.35),transparent_42%),linear-gradient(135deg,#eff6ff,#ffffff_58%,#f8fafc)] shadow-[0_28px_80px_rgba(37,99,235,0.12)]">
          <div className="grid gap-0 2xl:grid-cols-[1.15fr_0.85fr]">
            <div className="p-6 sm:p-8">
              <div className="inline-flex rounded-full border border-white/80 bg-white/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent-700 shadow-sm">
                Store pulse
              </div>
              <h2 className="mt-5 text-3xl font-semibold tracking-tight text-slate-950 sm:text-[2rem]">{store?.name ?? "Selected store"}</h2>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
                Keep approvals, sync health, and draft-heavy work coordinated from one dashboard with clear human checkpoints.
              </p>

              <div className="mt-6 grid gap-3 md:grid-cols-2">
                {workspaceHighlights.slice(0, 2).map(({ label, value, copy, icon: Icon }) => (
                  <div key={label} className="rounded-[1.5rem] border border-white/80 bg-white/86 p-4 shadow-sm backdrop-blur">
                    <div className="flex items-start gap-3">
                      <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-accent-50 text-accent-700">
                        <Icon className="h-4 w-4" />
                      </span>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
                        <p className="mt-2 break-words text-lg font-semibold leading-7 text-slate-950">{value}</p>
                        <p className="mt-1 text-sm leading-6 text-slate-500">{copy}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-white/70 bg-slate-950/[0.03] p-6 sm:p-8 2xl:border-l 2xl:border-t-0">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Operational snapshot</p>
              <div className="mt-5 grid gap-4 md:grid-cols-2 2xl:grid-cols-1">
                <div className="rounded-[1.5rem] border border-white/80 bg-white/82 p-4 shadow-sm">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-slate-700">Connection status</p>
                    <StatusPill value={store?.connection_status ?? "unknown"} />
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-500">
                    {summary.latest_sync_completed_at ? `Latest sync completed ${formatDate(summary.latest_sync_completed_at)}.` : "Run a sync to populate the store workspace."}
                  </p>
                </div>
                <div className="rounded-[1.5rem] border border-white/80 bg-white/82 p-4 shadow-sm">
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-rose-50 text-rose-600">
                      <ShieldAlert className="h-4 w-4" />
                    </span>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{workspaceHighlights[2].label}</p>
                      <p className="mt-1 text-2xl font-semibold text-slate-950">{workspaceHighlights[2].value}</p>
                    </div>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-500">{workspaceHighlights[2].copy}</p>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <SectionCard title="Recent activity">
          <ActivityTimeline items={activityItems} />
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.04fr)_minmax(21rem,0.96fr)]">
        <SectionCard title="Review-required workstreams">
          <div className="space-y-4">
            <div className="rounded-[1.35rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(248,250,252,0.98),rgba(239,246,255,0.82))] px-5 py-4">
              <p className="text-sm font-semibold text-slate-950">Human checkpoints across the store workspace</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Use the dashboard as a routing layer for draft-heavy work, flagged workflows, and operator approvals that still need a person in the loop.
              </p>
            </div>

            <div className="space-y-3">
              <DashboardNavCard
                title="Catalog drafts"
                description="Generate, edit, and submit product content drafts for approval."
                href={`/app/catalog/${selectedStoreId}/products`}
                count={summary.product_count}
                icon={Boxes}
              />
              <DashboardNavCard
                title="Support workspace"
                description="Open grounded reply drafts and operator review queues."
                href={`/app/support/${selectedStoreId}/conversations`}
                count={summary.customer_count}
                tone="neutral"
                icon={Wrench}
              />
              <DashboardNavCard
                title="Fraud review"
                description="Inspect high-risk orders and record internal decisions."
                href={`/app/fraud/${selectedStoreId}/reviews`}
                count={summary.recent_workflow_failures}
                tone={summary.recent_workflow_failures > 0 ? "danger" : "neutral"}
                icon={ShieldAlert}
              />
              <DashboardNavCard
                title="Inventory follow-up"
                description="Review low-stock alerts and supplier drafts."
                href={`/app/inventory/${selectedStoreId}`}
                count={summary.low_inventory_count}
                tone={summary.low_inventory_count > 0 ? "warning" : "success"}
                icon={Workflow}
              />
            </div>
          </div>
        </SectionCard>

        <div className="space-y-6">
          <DetailPanel title="Store health snapshot" subtitle="Current store context and the operating surface behind this workspace">
            <div className="space-y-4">
              <div className="rounded-[1.3rem] border border-slate-200 bg-slate-50/80">
                {[
                  { label: "Store", value: store?.name ?? "Selected store" },
                  { label: "Domain", value: store?.domain ?? "Unknown" },
                  { label: "Connection", value: <StatusPill value={store?.connection_status ?? "unknown"} /> }
                ].map((item, index) => (
                  <div key={item.label} className={`flex items-start justify-between gap-4 px-4 py-3 ${index ? "border-t border-slate-200" : ""}`}>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{item.label}</p>
                    <div className="max-w-[14rem] text-right text-sm text-slate-800">{item.value}</div>
                  </div>
                ))}
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-[1.2rem] border border-slate-200 bg-slate-50 px-4 py-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Products</p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{summary.product_count}</p>
                </div>
                <div className="rounded-[1.2rem] border border-slate-200 bg-slate-50 px-4 py-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Orders</p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{summary.order_count}</p>
                </div>
                <div className="rounded-[1.2rem] border border-slate-200 bg-slate-50 px-4 py-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Customers</p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{summary.customer_count}</p>
                </div>
              </div>
            </div>
          </DetailPanel>

          <SectionCard title="Operational scorecard">
            <div className="space-y-3">
              {dashboardSignals.map((signal) => (
                <DashboardMetricBand
                  key={signal.label}
                  label={signal.label}
                  value={signal.value}
                  detail={signal.detail}
                  tone={signal.tone}
                />
              ))}
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}

export function StoreListPage() {
  const navigate = useNavigate();
  const { me } = useAuth();
  const { selectedStoreId, setSelectedStoreId } = useAppState();
  const [form, setForm] = React.useState({
    name: "",
    domain: "",
    currency: "USD",
    timezone: "UTC"
  });

  const storesQuery = useStoresList();
  const createStore = useCreateStore((store) => {
    setSelectedStoreId(store.id);
    navigate(`/app/stores/${store.id}`);
    setForm({ name: "", domain: "", currency: "USD", timezone: "UTC" });
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
              createStore.mutate({
                name: form.name,
                domain: form.domain,
                currency: form.currency,
                timezone: form.timezone
              });
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

  const storeQuery = useStore(storeId);

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

  const integrationQuery = useStoreIntegration(storeId);
  const installUrlMutation = useCreateStoreInstallUrl(storeId);

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
  const [selectedRunId, setSelectedRunId] = React.useState<string | null>(null);

  const runsQuery = useStoreSyncRuns(storeId);
  const selectedRunQuery = useStoreSyncRun(storeId, selectedRunId);
  const triggerRun = useTriggerStoreSync(storeId, (run) => {
    setSelectedRunId(run.id);
  });
  const retryRun = useRetryStoreSyncRun(storeId, (run) => {
    setSelectedRunId(run.id);
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
                  className={`w-full rounded-2xl border p-4 text-left transition ${selectedRun?.id === run.id ? "border-accent-300 bg-accent-50" : "border-slate-200 bg-white hover:border-accent-200"
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
