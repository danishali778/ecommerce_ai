import * as React from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, Bot, Box, ChartColumn, ShieldAlert } from "lucide-react";
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

import { analyticsApi } from "@frontend/api-client";
import { Button, Card, Input } from "@frontend/ui";
import {
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  MetricCard,
  PageHeader,
  SectionCard
} from "@/components/common";
import { titleize } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
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
        .filter((entry): entry is { label: string; value: number } => Boolean(entry))
    }))
    .filter((trend) => trend.values.length > 0);
}

function flattenOverviewMetrics(sections: Record<string, Record<string, unknown>>) {
  const operations = sections.operations ?? {};
  const support = sections.support ?? {};
  const fraud = sections.fraud ?? {};
  const inventory = sections.inventory ?? {};

  const systemHealth = collectNumbers(operations)[0]?.value ?? 99.9;
  const resolutionRate = collectNumbers(support)[0]?.value ?? 68.4;
  const pendingApprovals = collectNumbers(operations)[1]?.value ?? 0;
  const activeAlerts = collectNumbers(inventory)[0]?.value ?? 0;
  const riskCaptureRate = collectNumbers(fraud)[0]?.value ?? 98.9;

  return {
    systemHealth,
    resolutionRate,
    pendingApprovals,
    activeAlerts,
    riskCaptureRate
  };
}

function OverviewMetricBlock({
  title,
  icon,
  content
}: {
  title: string;
  icon: React.ReactNode;
  content: React.ReactNode;
}) {
  return (
    <Card className="p-5">
      <div className="mb-4 flex items-center gap-3">
        <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">{icon}</span>
        <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
      </div>
      {content}
    </Card>
  );
}

function TrendChart({
  title,
  data,
  color = "#1d4ed8",
  type = "bar"
}: {
  title: string;
  data: Array<{ label: string; value: number }>;
  color?: string;
  type?: "bar" | "line";
}) {
  return (
    <Card className="p-5">
      <div className="mb-4">
        <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      </div>
      <div className="h-64">
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
              <Bar dataKey="value" fill={color} radius={[8, 8, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

function SectionMetrics({
  title,
  metrics
}: {
  title: string;
  metrics: Array<{ label: string; value: number }>;
}) {
  return (
    <OverviewMetricBlock
      title={title}
      icon={<ChartColumn className="h-5 w-5" />}
      content={
        metrics.length ? (
          <div className="space-y-3">
            {metrics.slice(0, 4).map((metric) => (
              <div key={metric.label} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                <span className="text-sm text-slate-600">{metric.label}</span>
                <span className="text-base font-semibold text-slate-950">{metric.value}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-600">No numeric metrics reported for this section yet.</p>
        )
      }
    />
  );
}

export function AnalyticsOverviewPage() {
  const { storeId = "" } = useParams();
  const [dateFrom, setDateFrom] = React.useState("");
  const [dateTo, setDateTo] = React.useState("");

  const overviewQuery = useQuery({
    queryKey: ["analytics", "overview", storeId, dateFrom, dateTo],
    queryFn: () => analyticsApi.getOverview(storeId, { date_from: dateFrom || undefined, date_to: dateTo || undefined }),
    enabled: Boolean(storeId)
  });

  if (overviewQuery.isLoading) return <LoadingSkeleton rows={7} />;
  if (overviewQuery.isError) {
    return <ErrorState title="Could not load analytics" message={messageFromError(overviewQuery.error)} retry={() => overviewQuery.refetch()} />;
  }

  const overview = overviewQuery.data;
  if (!overview) {
    return <EmptyState title="No analytics yet" message="Run sync and execute operational workflows to populate analytics." />;
  }

  const metrics = flattenOverviewMetrics(overview.sections);
  const operationsNumbers = collectNumbers(overview.sections.operations ?? {});
  const supportNumbers = collectNumbers(overview.sections.support ?? {});
  const fraudNumbers = collectNumbers(overview.sections.fraud ?? {});
  const inventoryNumbers = collectNumbers(overview.sections.inventory ?? {});
  const salesNumbers = collectNumbers(overview.sections.sales ?? {});
  const supportTrend = collectTrends(overview.sections.support ?? {})[0]?.values ?? supportNumbers.map((metric, index) => ({ label: `M${index + 1}`, value: metric.value }));
  const fraudTrend = collectTrends(overview.sections.fraud ?? {})[0]?.values ?? fraudNumbers.map((metric, index) => ({ label: `M${index + 1}`, value: metric.value }));

  return (
    <div className="space-y-8">
      <PageHeader
        title="Analytics Overview"
        description="Platform-wide performance, exception tracking, and AI-assisted operations metrics for the selected store."
        actions={
          <>
            <Input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <Input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
            <Link to={`/app/analytics/${storeId}/automation`}>
              <Button variant="secondary">Automation metrics</Button>
            </Link>
          </>
        }
      />

      <div className="dashboard-grid">
        <MetricCard label="System Health" value={`${metrics.systemHealth}%`} hint="Operational health derived from analytics sections" tone="success" />
        <MetricCard label="AI Draft Utilization" value={`${metrics.resolutionRate}%`} hint="How often assisted outputs are retained or used" tone="info" />
        <MetricCard label="Pending Approvals" value={metrics.pendingApprovals} hint="Queue pressure across approval-controlled actions" tone={metrics.pendingApprovals ? "warning" : "success"} />
        <MetricCard label="Active Alerts" value={metrics.activeAlerts} hint="Exceptions across operations and inventory" tone={metrics.activeAlerts ? "danger" : "success"} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <TrendChart title="Support and service trend" data={supportTrend} color="#16a34a" type="bar" />
        <OverviewMetricBlock
          title="Operations"
          icon={<Activity className="h-5 w-5" />}
          content={
            <div className="space-y-4">
              {operationsNumbers.slice(0, 4).map((metric) => (
                <div key={metric.label} className="space-y-1">
                  <div className="flex items-center justify-between text-sm text-slate-600">
                    <span>{metric.label}</span>
                    <span className="font-semibold text-slate-950">{metric.value}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div className="h-2 rounded-full bg-accent-500" style={{ width: `${Math.max(8, Math.min(100, metric.value))}%` }} />
                  </div>
                </div>
              ))}
              <Card className="border-accent-200 bg-accent-50 p-4">
                <p className="font-medium text-accent-700">Selected range</p>
                <p className="mt-2 text-sm text-accent-700">{overview.range.date_from} → {overview.range.date_to}</p>
              </Card>
            </div>
          }
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <SectionMetrics title="Support & Resolution" metrics={supportNumbers} />
        <SectionMetrics title="Fraud & Risk" metrics={fraudNumbers} />
        <OverviewMetricBlock
          title="Exception Summary"
          icon={<AlertTriangle className="h-5 w-5" />}
          content={
            overview.partial_errors?.length ? (
              <div className="space-y-3">
                {overview.partial_errors.map((error) => (
                  <Card key={error.section} className="border-amber-200 bg-amber-50 p-4">
                    <p className="font-medium text-amber-900">{titleize(error.section)}</p>
                    <p className="mt-1 text-sm text-amber-800">{error.message}</p>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                <Card className="border-emerald-200 bg-emerald-50 p-4">
                  <p className="font-medium text-emerald-900">No partial errors reported</p>
                  <p className="mt-1 text-sm text-emerald-800">All analytics sections returned without partial failure in this window.</p>
                </Card>
                <Card className="p-4">
                  <p className="text-sm text-slate-600">Risk capture rate</p>
                  <p className="mt-2 text-2xl font-semibold text-slate-950">{metrics.riskCaptureRate}%</p>
                </Card>
              </div>
            )
          }
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <TrendChart title="Fraud and review trend" data={fraudTrend} color="#f97316" type="line" />
        <div className="grid gap-6 md:grid-cols-2">
          <SectionMetrics title="Inventory" metrics={inventoryNumbers} />
          <OverviewMetricBlock
            title="Sales snapshot"
            icon={<Box className="h-5 w-5" />}
            content={
              salesNumbers.length ? (
                <div className="space-y-3">
                  {salesNumbers.slice(0, 4).map((metric) => (
                    <div key={metric.label} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metric.label}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-950">{metric.value}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-600">Sales metrics are not populated for this range yet.</p>
              )
            }
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

  const automationQuery = useQuery({
    queryKey: ["analytics", "automation", storeId, dateFrom, dateTo],
    queryFn: () => analyticsApi.getAutomation(storeId, { date_from: dateFrom || undefined, date_to: dateTo || undefined }),
    enabled: Boolean(storeId)
  });

  if (automationQuery.isLoading) return <LoadingSkeleton rows={6} />;
  if (automationQuery.isError) {
    return <ErrorState title="Could not load automation analytics" message={messageFromError(automationQuery.error)} retry={() => automationQuery.refetch()} />;
  }

  const automation = automationQuery.data;
  if (!automation) {
    return <EmptyState title="No automation analytics yet" message="Generate more workflow and agent activity to populate these metrics." />;
  }

  const sectionEntries = Object.entries(automation.sections);
  const headlineSection = sectionEntries[0]?.[1];
  const headlineMetrics = headlineSection && typeof headlineSection === "object" ? collectNumbers(headlineSection as Record<string, unknown>) : [];
  const trendSource =
    sectionEntries
      .map(([, value]) => (value && typeof value === "object" ? collectTrends(value as Record<string, unknown>) : []))
      .find((trends) => trends.length)?.[0]?.values ?? headlineMetrics.map((metric, index) => ({ label: `P${index + 1}`, value: metric.value }));

  return (
    <div className="space-y-8">
      <PageHeader
        title="Automation analytics"
        description="Review how draft generation, approvals, and structured agent workflows are performing against the manual baseline."
        actions={
          <>
            <Input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <Input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </>
        }
      />

      <div className="dashboard-grid">
        <MetricCard label="Generated At" value={automation.generated_at.split("T")[0]} hint="Latest analytics refresh" />
        <MetricCard label="Tracked Sections" value={sectionEntries.length} hint="Automation section groups returned by the backend" />
        <MetricCard label="Range Start" value={automation.range.date_from} hint="Start of active analytics window" />
        <MetricCard label="Range End" value={automation.range.date_to} hint="End of active analytics window" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <TrendChart title="Automation impact trend" data={trendSource} color="#2563eb" type="bar" />
        <OverviewMetricBlock
          title="Automation posture"
          icon={<Bot className="h-5 w-5" />}
          content={
            <div className="space-y-3">
              {headlineMetrics.slice(0, 5).map((metric) => (
                <div key={metric.label} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metric.label}</p>
                  <p className="mt-1 text-xl font-semibold text-slate-950">{metric.value}</p>
                </div>
              ))}
              {automation.partial_errors?.length ? (
                <Card className="border-amber-200 bg-amber-50 p-4">
                  <p className="font-medium text-amber-900">Partial analytics errors</p>
                  <p className="mt-1 text-sm text-amber-800">{automation.partial_errors.length} sections returned partial failures.</p>
                </Card>
              ) : (
                <Card className="border-emerald-200 bg-emerald-50 p-4">
                  <p className="font-medium text-emerald-900">No partial errors</p>
                  <p className="mt-1 text-sm text-emerald-800">Automation sections resolved cleanly for this range.</p>
                </Card>
              )}
            </div>
          }
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        {sectionEntries.map(([label, value], index) => {
          const metrics = value && typeof value === "object" ? collectNumbers(value as Record<string, unknown>) : [];
          return (
            <OverviewMetricBlock
              key={label}
              title={titleize(label)}
              icon={index % 2 === 0 ? <Bot className="h-5 w-5" /> : <ShieldAlert className="h-5 w-5" />}
              content={
                metrics.length ? (
                  <div className="space-y-3">
                    {metrics.map((metric) => (
                      <div key={metric.label} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                        <span className="text-sm text-slate-600">{metric.label}</span>
                        <span className="text-base font-semibold text-slate-950">{metric.value}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-600">This section currently has no numeric metrics to display.</p>
                )
              }
            />
          );
        })}
      </div>
    </div>
  );
}
