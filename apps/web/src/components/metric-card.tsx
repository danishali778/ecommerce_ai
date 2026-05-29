import { Card, cn } from "@frontend/ui";

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
