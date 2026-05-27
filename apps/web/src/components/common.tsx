import * as React from "react";

import { Avatar, Badge, Button, Card, ProgressBar, cn } from "@frontend/ui";

export function PageHeader({
  title,
  description,
  actions
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div className="space-y-1">
        <h1 className="section-title">{title}</h1>
        {description ? <p className="section-copy max-w-3xl">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
    </div>
  );
}

export function MetricCard({
  label,
  value,
  hint,
  tone = "neutral"
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "neutral" | "info" | "success" | "warning" | "danger";
}) {
  const accentMap = {
    neutral: "border-slate-200",
    info: "border-blue-200",
    success: "border-emerald-200",
    warning: "border-amber-200",
    danger: "border-rose-200"
  };
  return (
    <Card className={cn("p-5", accentMap[tone])}>
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-slate-950">{value}</p>
      {hint ? <p className="mt-2 text-sm text-slate-600">{hint}</p> : null}
    </Card>
  );
}

export function StatusPill({ value }: { value: string }) {
  const normalized = value.toLowerCase();
  const tone =
    normalized.includes("success") || normalized.includes("ready") || normalized.includes("approved") || normalized.includes("resolved")
      ? "success"
      : normalized.includes("fail") || normalized.includes("rejected") || normalized.includes("critical")
        ? "danger"
        : normalized.includes("review") || normalized.includes("pending") || normalized.includes("queue")
          ? "warning"
          : "info";
  return <Badge tone={tone}>{value.replaceAll("_", " ")}</Badge>;
}

export function KeyValueGrid({ items }: { items: Array<{ label: string; value: React.ReactNode }> }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {items.map((item) => (
        <div key={item.label} className="space-y-1 rounded-xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{item.label}</p>
          <div className="text-sm text-slate-800">{item.value}</div>
        </div>
      ))}
    </div>
  );
}

export function EmptyState({
  title,
  message,
  action
}: {
  title: string;
  message: string;
  action?: React.ReactNode;
}) {
  return (
    <Card className="flex min-h-56 flex-col items-center justify-center gap-3 p-8 text-center">
      <p className="text-xl font-semibold text-slate-950">{title}</p>
      <p className="max-w-xl text-sm text-slate-600">{message}</p>
      {action}
    </Card>
  );
}

export function ErrorState({ title, message, retry }: { title: string; message: string; retry?: () => void }) {
  return (
    <Card className="border-rose-200 bg-rose-50 p-6">
      <p className="text-lg font-semibold text-rose-800">{title}</p>
      <p className="mt-2 text-sm text-rose-700">{message}</p>
      {retry ? (
        <Button className="mt-4" variant="danger" onClick={retry}>
          Try Again
        </Button>
      ) : null}
    </Card>
  );
}

export function LoadingSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-16 animate-pulse rounded-2xl bg-slate-100" />
      ))}
    </div>
  );
}

export function DetailPanel({
  title,
  subtitle,
  children
}: React.PropsWithChildren<{ title: string; subtitle?: string }>) {
  return (
    <Card className="p-5">
      <div className="mb-4 space-y-1">
        <h2 className="text-xl font-semibold text-slate-950">{title}</h2>
        {subtitle ? <p className="text-sm text-slate-600">{subtitle}</p> : null}
      </div>
      {children}
    </Card>
  );
}

export function SectionCard({
  title,
  actions,
  children
}: React.PropsWithChildren<{ title: string; actions?: React.ReactNode }>) {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
        {actions}
      </div>
      <div className="p-5">{children}</div>
    </Card>
  );
}

export function Table({
  headers,
  rows
}: {
  headers: string[];
  rows: Array<React.ReactNode[]>;
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200">
      <div className="grid bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500" style={{ gridTemplateColumns: `repeat(${headers.length}, minmax(0, 1fr))` }}>
        {headers.map((header) => (
          <div key={header}>{header}</div>
        ))}
      </div>
      <div className="divide-y divide-slate-200">
        {rows.map((row, rowIndex) => (
          <div key={rowIndex} className="grid gap-3 px-4 py-4 text-sm text-slate-800" style={{ gridTemplateColumns: `repeat(${headers.length}, minmax(0, 1fr))` }}>
            {row.map((cell, cellIndex) => (
              <div key={cellIndex}>{cell}</div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function ActivityTimeline({ items }: { items: Array<{ title: string; description: string; created_at: string }> }) {
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={`${item.title}-${item.created_at}`} className="relative border-l border-slate-200 pl-4">
          <span className="absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full bg-accent-500" />
          <p className="font-medium text-slate-950">{item.title}</p>
          <p className="mt-1 text-sm text-slate-600">{item.description}</p>
          <p className="mt-1 text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
}

export function RuntimeRunCard({
  title,
  status,
  meta,
  body
}: {
  title: string;
  status: string;
  meta?: string;
  body?: React.ReactNode;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-950">{title}</p>
          {meta ? <p className="mt-1 text-sm text-slate-600">{meta}</p> : null}
        </div>
        <StatusPill value={status} />
      </div>
      {body ? <div className="mt-4 text-sm text-slate-700">{body}</div> : null}
    </Card>
  );
}

export function ReviewRequiredBanner({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{message}</div>
  );
}

export function DraftStatusBanner({ status, modelName }: { status: string; modelName?: string }) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-blue-200 bg-blue-50 px-4 py-3">
      <div>
        <p className="text-sm font-medium text-blue-900">Draft status: {status.replaceAll("_", " ")}</p>
        {modelName ? <p className="text-xs text-blue-700">Generated by {modelName}</p> : null}
      </div>
      <StatusPill value={status} />
    </div>
  );
}

export function PolicyCitationCard({ title, body }: { title: string; body: string }) {
  return (
    <Card className="border-blue-100 bg-blue-50 p-4">
      <p className="font-medium text-blue-900">{title}</p>
      <p className="mt-2 text-sm text-blue-800">{body}</p>
    </Card>
  );
}

export function RiskFactorCard({ title, body }: { title: string; body: string }) {
  return (
    <Card className="border-rose-100 bg-rose-50 p-4">
      <p className="font-medium text-rose-900">{title}</p>
      <p className="mt-2 text-sm text-rose-800">{body}</p>
    </Card>
  );
}

export function SupplierDraftCard({ subject, body }: { subject: string; body: string }) {
  return (
    <Card className="p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Supplier Draft</p>
      <p className="mt-2 font-medium text-slate-900">{subject}</p>
      <pre className="mt-3 whitespace-pre-wrap text-sm text-slate-700">{body}</pre>
    </Card>
  );
}

export function TopStat({
  label,
  value,
  percent
}: {
  label: string;
  value: number;
  percent: number;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm text-slate-600">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <ProgressBar value={percent} />
    </div>
  );
}

export function UserPill({ name }: { name: string }) {
  return (
    <div className="inline-flex items-center gap-2">
      <Avatar name={name} />
      <span>{name}</span>
    </div>
  );
}
