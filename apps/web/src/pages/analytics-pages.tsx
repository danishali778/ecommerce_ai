import * as React from "react";
import { Link, useParams } from "react-router-dom";
import { Activity, AlertTriangle, Bot, Boxes, ChartColumn, Clock3, MessagesSquare, ShieldAlert, Sparkles } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { Button, Card, Input } from "@frontend/ui";

import { useAnalyticsAutomation, useAnalyticsOverview } from "@/hooks/use-analytics";
import { EmptyState, ErrorState, LoadingSkeleton, PageHeader, SectionCard } from "@/components/common";
import { titleize } from "@/lib/format";

type NumericMetric = {
  key: string;
  label: string;
  value: number;
};

type TrendPoint = {
  label: string;
  value: number;
};

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function formatDateLabel(value: string | null | undefined) {
  if (!value) return "-";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(parsed);
}

function formatDateTimeLabel(value: string | null | undefined) {
  if (!value) return "-";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(parsed);
}

function formatRangeLabel(range: { date_from: string; date_to: string }) {
  return `${formatDateLabel(range.date_from)} to ${formatDateLabel(range.date_to)}`;
}

function countRangeDays(range: { date_from: string; date_to: string }) {
  const start = new Date(range.date_from);
  const end = new Date(range.date_to);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0;
  const diff = Math.abs(end.getTime() - start.getTime());
  return Math.max(1, Math.round(diff / 86400000));
}

function collectNumbers(record: Record<string, unknown>) {
  return Object.entries(record)
    .filter(([, value]) => typeof value === "number")
    .map(([key, value]) => ({
      key,
      label: titleize(key),
      value: value as number
    }));
}

function collectTrends(record: Record<string, unknown>) {
  return Object.entries(record)
    .flatMap(([key, value]) => (Array.isArray(value) ? [[key, value] as const] : []))
    .map(([key, value]) => ({
      key,
      values: value
        .map((entry, index) => {
          if (typeof entry === "number") return { label: `P${index + 1}`, value: entry };
          if (entry && typeof entry === "object") {
            const objectEntry = entry as Record<string, unknown>;
            const numeric = Object.entries(objectEntry).find(([, candidate]) => typeof candidate === "number");
            return {
              label: String(objectEntry.label ?? objectEntry.date ?? objectEntry.name ?? `P${index + 1}`),
              value: typeof numeric?.[1] === "number" ? (numeric[1] as number) : 0
            };
          }
          return null;
        })
        .filter((entry): entry is TrendPoint => Boolean(entry))
    }))
    .filter((trend) => trend.values.length > 0);
}

function readMetric(record: Record<string, unknown>, keys: string[], fallback = 0) {
  for (const key of keys) {
    const candidate = record[key];
    if (typeof candidate === "number") return candidate;
  }

  const firstNumeric = Object.values(record).find((candidate) => typeof candidate === "number");
  return typeof firstNumeric === "number" ? firstNumeric : fallback;
}

function sum(values: number[]) {
  return values.reduce((total, value) => total + value, 0);
}

function AnalyticsRangeBar({
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
  action
}: {
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  action?: React.ReactNode;
}) {
  return (
    <div className="surface-panel p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-2">
            <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">From</span>
            <Input type="date" value={dateFrom} onChange={(event) => onDateFromChange(event.target.value)} />
          </label>
          <label className="space-y-2">
            <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">To</span>
            <Input type="date" value={dateTo} onChange={(event) => onDateToChange(event.target.value)} />
          </label>
        </div>
        {action ? <div className="flex flex-wrap gap-3 lg:justify-end">{action}</div> : null}
      </div>
    </div>
  );
}

function HeadlineMetric({
  label,
  value,
  detail,
  tone = "slate"
}: {
  label: string;
  value: React.ReactNode;
  detail: string;
  tone?: "slate" | "blue" | "emerald" | "amber";
}) {
  const toneClass =
    tone === "blue"
      ? "border-blue-200 bg-blue-50/80"
      : tone === "emerald"
        ? "border-emerald-200 bg-emerald-50/80"
        : tone === "amber"
          ? "border-amber-200 bg-amber-50/80"
          : "border-slate-200 bg-white";

  return (
    <div className={`rounded-[1.35rem] border px-5 py-5 ${toneClass}`}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{detail}</p>
    </div>
  );
}

function SignalCard({
  eyebrow,
  title,
  description,
  children
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="surface-panel overflow-hidden p-5">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{eyebrow}</p>
      <h3 className="mt-3 text-xl font-semibold tracking-tight text-slate-950">{title}</h3>
      <p className="mt-2 text-sm leading-7 text-slate-600">{description}</p>
      <div className="mt-5">{children}</div>
    </div>
  );
}

function MetricsList({
  metrics,
  emptyMessage
}: {
  metrics: NumericMetric[];
  emptyMessage: string;
}) {
  if (!metrics.length) {
    return <p className="text-sm text-slate-600">{emptyMessage}</p>;
  }

  return (
    <div className="space-y-3">
      {metrics.slice(0, 5).map((metric) => (
        <div key={metric.label} className="flex items-center justify-between rounded-[1.1rem] border border-slate-200 bg-slate-50 px-4 py-3">
          <span className="text-sm text-slate-600">{metric.label}</span>
          <span className="text-base font-semibold text-slate-950">{metric.value}</span>
        </div>
      ))}
    </div>
  );
}

function TrendChart({
  title,
  description,
  data,
  color = "#2563eb",
  type = "bar"
}: {
  title: string;
  description: string;
  data: TrendPoint[];
  color?: string;
  type?: "bar" | "line";
}) {
  return (
    <div className="surface-panel p-5">
      <div className="mb-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{title}</p>
        <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
      </div>
      <div className="h-72">
        {data.length ? (
          <ResponsiveContainer width="100%" height="100%">
            {type === "line" ? (
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 12 }} />
                <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke={color} strokeWidth={3} dot={{ r: 3 }} />
              </LineChart>
            ) : (
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 12 }} />
                <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="value" fill={color} radius={[10, 10, 0, 0]} />
              </BarChart>
            )}
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center rounded-[1.25rem] border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-500">
            Trend data is not populated for this range yet.
          </div>
        )}
      </div>
    </div>
  );
}

function ExceptionSummary({
  partialErrors,
  fallbackTitle,
  fallbackDescription,
  accentValue,
  accentLabel
}: {
  partialErrors?: Array<{ section: string; message: string }> | null;
  fallbackTitle: string;
  fallbackDescription: string;
  accentValue: number;
  accentLabel: string;
}) {
  return (
    <SignalCard
      eyebrow="Exception summary"
      title="Operational exceptions"
      description="Use this rail to spot missing sections, partial failures, and the areas that still need operator attention."
    >
      {partialErrors?.length ? (
        <div className="space-y-3">
          {partialErrors.map((error) => (
            <Card key={error.section} className="border-amber-200 bg-amber-50 p-4">
              <p className="font-medium text-amber-900">{titleize(error.section)}</p>
              <p className="mt-1 text-sm leading-6 text-amber-800">{error.message}</p>
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <Card className="border-emerald-200 bg-emerald-50 p-4">
            <p className="font-medium text-emerald-900">{fallbackTitle}</p>
            <p className="mt-1 text-sm leading-6 text-emerald-800">{fallbackDescription}</p>
          </Card>
          <Card className="p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{accentLabel}</p>
            <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{accentValue}</p>
          </Card>
        </div>
      )}
    </SignalCard>
  );
}

function AnalyticsSection({
  eyebrow,
  title,
  description,
  icon,
  metrics,
  emptyMessage
}: {
  eyebrow: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  metrics: NumericMetric[];
  emptyMessage: string;
}) {
  return (
    <SignalCard eyebrow={eyebrow} title={title} description={description}>
      <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-slate-700">
        {icon}
      </div>
      <MetricsList metrics={metrics} emptyMessage={emptyMessage} />
    </SignalCard>
  );
}

export function AnalyticsOverviewPage() {
  const { storeId = "" } = useParams();
  const [dateFrom, setDateFrom] = React.useState("");
  const [dateTo, setDateTo] = React.useState("");

  const overviewQuery = useAnalyticsOverview(storeId, { date_from: dateFrom || undefined, date_to: dateTo || undefined });

  if (overviewQuery.isLoading) return <LoadingSkeleton rows={7} />;
  if (overviewQuery.isError) {
    return <ErrorState title="Could not load analytics" message={messageFromError(overviewQuery.error)} retry={() => overviewQuery.refetch()} />;
  }

  const overview = overviewQuery.data;
  if (!overview) {
    return <EmptyState title="No analytics yet" message="Run sync and execute operational workflows to populate analytics." />;
  }

  const operations = overview.sections.operations ?? {};
  const support = overview.sections.support ?? {};
  const fraud = overview.sections.fraud ?? {};
  const inventory = overview.sections.inventory ?? {};
  const sales = overview.sections.sales ?? {};

  const operationsNumbers = collectNumbers(operations);
  const supportNumbers = collectNumbers(support);
  const fraudNumbers = collectNumbers(fraud);
  const inventoryNumbers = collectNumbers(inventory);
  const salesNumbers = collectNumbers(sales);

  const supportTrend = collectTrends(support)[0]?.values ?? supportNumbers.map((metric, index) => ({ label: `P${index + 1}`, value: metric.value }));
  const fraudTrend = collectTrends(fraud)[0]?.values ?? fraudNumbers.map((metric, index) => ({ label: `P${index + 1}`, value: metric.value }));

  const ordersInWindow = readMetric(sales, ["order_count"]);
  const openConversations = readMetric(support, ["open_conversation_count"]);
  const draftAssistCount = readMetric(support, ["support_drafts_generated_count"]);
  const activeAlerts = sum([
    readMetric(inventory, ["open_low_stock_alert_count"]),
    readMetric(inventory, ["open_reorder_suggestion_count"], 0)
  ]);
  const reviewQueues = sum([
    readMetric(operations, ["pending_approval_count"]),
    readMetric(support, ["pending_support_review_count"], 0),
    readMetric(fraud, ["pending_risk_review_count"], 0)
  ]);
  const highRiskOrders = readMetric(fraud, ["high_risk_order_count"], 0);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Analytics Overview"
        description="Review live operational volume, human review pressure, inventory exceptions, and AI-assisted workflow activity for the active store."
        actions={
          <Link to={`/app/analytics/${storeId}/automation`}>
            <Button variant="secondary">Automation metrics</Button>
          </Link>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(20rem,0.92fr)]">
        <div className="surface-panel overflow-hidden border-accent-200 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.2),transparent_42%),linear-gradient(135deg,#eff6ff,#ffffff_58%,#f8fafc)] p-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/90 bg-white/90 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-accent-700">
            <ChartColumn className="h-3.5 w-3.5" />
            Performance cockpit
          </div>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight text-slate-950">A cleaner read on the store instead of disconnected counters.</h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
            The analytics workspace now centers on actual workload and exception signals, so operators can see what is open, what is blocked, and where AI assistance is already active.
          </p>
        </div>

        <div className="surface-panel p-5">
          <div className="space-y-4">
            <div className="rounded-[1.15rem] border border-slate-200 bg-slate-50 px-4 py-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Selected range</p>
              <p className="mt-2 text-lg font-semibold tracking-tight text-slate-950">{formatRangeLabel(overview.range)}</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">Use the filters below to narrow what the operator team is reviewing.</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <div className="rounded-[1.15rem] border border-slate-200 bg-white px-4 py-4">
                <div className="flex items-center gap-2 text-slate-500">
                  <Clock3 className="h-4 w-4" />
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em]">Generated at</p>
                </div>
                <p className="mt-2 text-sm font-medium text-slate-800">{formatDateTimeLabel(overview.generated_at)}</p>
              </div>
              <div className="rounded-[1.15rem] border border-slate-200 bg-white px-4 py-4">
                <div className="flex items-center gap-2 text-slate-500">
                  <Sparkles className="h-4 w-4" />
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em]">Human review queues</p>
                </div>
                <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{reviewQueues}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <AnalyticsRangeBar
        dateFrom={dateFrom}
        dateTo={dateTo}
        onDateFromChange={setDateFrom}
        onDateToChange={setDateTo}
        action={
          <Link to={`/app/analytics/${storeId}/automation`}>
            <Button>Open automation breakdown</Button>
          </Link>
        }
      />

      <div className="grid gap-4 xl:grid-cols-4">
        <HeadlineMetric label="Orders in window" value={ordersInWindow} detail="Commerce volume captured in the current reporting range." tone="blue" />
        <HeadlineMetric label="Open conversations" value={openConversations} detail="Support conversations still active for human follow-through." tone="emerald" />
        <HeadlineMetric label="Draft assists" value={draftAssistCount} detail="AI-assisted outputs already generated for operator review." />
        <HeadlineMetric label="Inventory exceptions" value={activeAlerts} detail="Combined low-stock and reorder work that still needs attention." tone="amber" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(20rem,0.9fr)]">
        <TrendChart
          title="Support activity trend"
          description="This view tracks how support workload and AI-assisted throughput evolve across the selected reporting window."
          data={supportTrend}
          color="#16a34a"
          type="bar"
        />
        <SignalCard
          eyebrow="Priority watch"
          title="What needs human review now"
          description="These are the clearest high-friction signals in the current store context."
        >
          <div className="space-y-3">
            <Card className="border-slate-200 bg-slate-50 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Pending approvals</p>
              <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{readMetric(operations, ["pending_approval_count"])}</p>
            </Card>
            <Card className="border-slate-200 bg-slate-50 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Pending support reviews</p>
              <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{readMetric(support, ["pending_support_review_count"])}</p>
            </Card>
            <Card className="border-slate-200 bg-slate-50 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">High-risk orders</p>
              <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{highRiskOrders}</p>
            </Card>
          </div>
        </SignalCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <AnalyticsSection
          eyebrow="Support"
          title="Support and resolution"
          description="Conversation volume, pending review work, and assisted draft generation live together here."
          icon={<MessagesSquare className="h-5 w-5" />}
          metrics={supportNumbers}
          emptyMessage="Support metrics are not populated for this range yet."
        />
        <AnalyticsSection
          eyebrow="Fraud"
          title="Fraud and risk"
          description="Risk signals and manual review pressure are grouped so operators can triage faster."
          icon={<ShieldAlert className="h-5 w-5" />}
          metrics={fraudNumbers}
          emptyMessage="Fraud metrics are not populated for this range yet."
        />
        <ExceptionSummary
          partialErrors={overview.partial_errors ?? null}
          fallbackTitle="No partial errors reported"
          fallbackDescription="All analytics sections resolved cleanly for the selected range."
          accentValue={reviewQueues}
          accentLabel="Review queues"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <TrendChart
          title="Fraud and review trend"
          description="Use this trend to compare how risk-related activity behaves against the current review workload."
          data={fraudTrend}
          color="#f97316"
          type="line"
        />
        <div className="grid gap-6 md:grid-cols-2">
          <AnalyticsSection
            eyebrow="Inventory"
            title="Inventory pressure"
            description="Inventory alerts and reorder pressure stay visible here so content or support work does not hide fulfillment risk."
            icon={<Boxes className="h-5 w-5" />}
            metrics={inventoryNumbers}
            emptyMessage="Inventory metrics are not populated for this range yet."
          />
          <AnalyticsSection
            eyebrow="Sales"
            title="Sales snapshot"
            description="A lightweight summary of sales-side operational signals for the same reporting window."
            icon={<Activity className="h-5 w-5" />}
            metrics={salesNumbers}
            emptyMessage="Sales metrics are not populated for this range yet."
          />
        </div>
      </div>
    </div>
  );
}

export function AnalyticsAutomationPage() {
  const { storeId = "" } = useParams();
  const [dateFrom, setDateFrom] = React.useState("");
  const [dateTo, setDateTo] = React.useState("");

  const automationQuery = useAnalyticsAutomation(storeId, { date_from: dateFrom || undefined, date_to: dateTo || undefined });

  if (automationQuery.isLoading) return <LoadingSkeleton rows={6} />;
  if (automationQuery.isError) {
    return <ErrorState title="Could not load automation analytics" message={messageFromError(automationQuery.error)} retry={() => automationQuery.refetch()} />;
  }

  const automation = automationQuery.data;
  if (!automation) {
    return <EmptyState title="No automation analytics yet" message="Generate more workflow and agent activity to populate these metrics." />;
  }

  const sectionEntries = Object.entries(automation.sections);
  const sectionMetrics = sectionEntries.map(([label, value]) => ({
    label,
    metrics: value && typeof value === "object" ? collectNumbers(value as Record<string, unknown>) : [],
    trends: value && typeof value === "object" ? collectTrends(value as Record<string, unknown>) : []
  }));

  const trendSource =
    sectionMetrics.find((section) => section.trends.length)?.trends[0]?.values ??
    sectionMetrics.flatMap((section) => section.metrics).slice(0, 5).map((metric, index) => ({ label: `P${index + 1}`, value: metric.value }));

  const totalTrackedMetrics = sectionMetrics.reduce((count, section) => count + section.metrics.length, 0);
  const partialErrorCount = automation.partial_errors?.length ?? 0;
  const totalSignalVolume = sum(sectionMetrics.flatMap((section) => section.metrics).map((metric) => metric.value));
  const largestSection = [...sectionMetrics].sort((left, right) => right.metrics.length - left.metrics.length)[0];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Automation Analytics"
        description="Review how structured automation, draft generation, and agent-driven operations are performing before they hit a human checkpoint."
        actions={
          <Link to={`/app/analytics/${storeId}`}>
            <Button variant="secondary">Back to overview</Button>
          </Link>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(20rem,0.92fr)]">
        <div className="surface-panel overflow-hidden border-accent-200 bg-[radial-gradient(circle_at_top_left,rgba(29,78,216,0.16),transparent_42%),linear-gradient(135deg,#eff6ff,#ffffff_58%,#f8fafc)] p-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/90 bg-white/90 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-accent-700">
            <Bot className="h-3.5 w-3.5" />
            Automation control
          </div>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight text-slate-950">See where automation is producing signal instead of just volume.</h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
            This view consolidates automation sections into a single operating surface so the team can understand where agents are generating meaningful output and where follow-up still breaks down.
          </p>
        </div>

        <div className="surface-panel p-5">
          <div className="space-y-4">
            <div className="rounded-[1.15rem] border border-slate-200 bg-slate-50 px-4 py-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Selected range</p>
              <p className="mt-2 text-lg font-semibold tracking-tight text-slate-950">{formatRangeLabel(automation.range)}</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">Use the same reporting window to compare automation impact against the main analytics overview.</p>
            </div>
            <div className="rounded-[1.15rem] border border-slate-200 bg-white px-4 py-4">
              <div className="flex items-center gap-2 text-slate-500">
                <Clock3 className="h-4 w-4" />
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em]">Generated at</p>
              </div>
              <p className="mt-2 text-sm font-medium text-slate-800">{formatDateTimeLabel(automation.generated_at)}</p>
            </div>
          </div>
        </div>
      </div>

      <AnalyticsRangeBar dateFrom={dateFrom} dateTo={dateTo} onDateFromChange={setDateFrom} onDateToChange={setDateTo} />

      <div className="grid gap-4 xl:grid-cols-4">
        <HeadlineMetric label="Tracked sections" value={sectionEntries.length} detail="Automation domains returned by the backend for this time window." tone="blue" />
        <HeadlineMetric label="Tracked metrics" value={totalTrackedMetrics} detail="Numeric automation signals currently available for review." />
        <HeadlineMetric label="Partial failures" value={partialErrorCount} detail="Sections that returned only a partial result or incomplete response." tone={partialErrorCount ? "amber" : "emerald"} />
        <HeadlineMetric label="Signal volume" value={totalSignalVolume} detail="Aggregate count across the current automation metrics set." />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(20rem,0.9fr)]">
        <TrendChart
          title="Automation impact trend"
          description="This chart keeps the most useful automation trend visible without forcing operators to read each section individually."
          data={trendSource}
          color="#2563eb"
          type="bar"
        />
        <SignalCard
          eyebrow="Largest section"
          title={largestSection ? titleize(largestSection.label) : "Automation posture"}
          description="The summary rail highlights the densest current automation signal set so you can spot the most active area first."
        >
          {largestSection ? (
            <MetricsList metrics={largestSection.metrics} emptyMessage="This section currently has no numeric metrics to display." />
          ) : (
            <p className="text-sm text-slate-600">No automation metrics are available yet.</p>
          )}
        </SignalCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <ExceptionSummary
          partialErrors={automation.partial_errors ?? null}
          fallbackTitle="No partial errors"
          fallbackDescription="Automation sections resolved cleanly for this reporting window."
          accentValue={sectionEntries.length}
          accentLabel="Sections returned"
        />
        <AnalyticsSection
          eyebrow="Operator posture"
          title="Automation guardrails"
          description="Keep an eye on the tracked section count and error posture before trusting the outputs downstream."
          icon={<AlertTriangle className="h-5 w-5" />}
          metrics={[
            { key: "sections", label: "Tracked sections", value: sectionEntries.length },
            { key: "metrics", label: "Tracked metrics", value: totalTrackedMetrics },
            { key: "errors", label: "Partial failures", value: partialErrorCount }
          ]}
          emptyMessage="Guardrail metrics are not available."
        />
        <AnalyticsSection
          eyebrow="Coverage"
          title="Reporting coverage"
          description="This summary keeps the automation window and trend depth understandable at a glance."
          icon={<Clock3 className="h-5 w-5" />}
          metrics={[
            { key: "window", label: "Window days", value: countRangeDays(automation.range) },
            { key: "trend_points", label: "Trend points", value: trendSource.length },
            { key: "largest_section", label: "Largest section metrics", value: largestSection?.metrics.length ?? 0 }
          ]}
          emptyMessage="Refresh metrics are not available."
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        {sectionMetrics.map((section, index) => (
          <AnalyticsSection
            key={section.label}
            eyebrow="Section detail"
            title={titleize(section.label)}
            description="A focused readout of the numeric metrics the backend returned for this automation section."
            icon={index % 2 === 0 ? <Bot className="h-5 w-5" /> : <ShieldAlert className="h-5 w-5" />}
            metrics={section.metrics}
            emptyMessage="This section currently has no numeric metrics to display."
          />
        ))}
      </div>
    </div>
  );
}
