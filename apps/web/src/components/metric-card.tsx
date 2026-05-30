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
    neutral: {
      border: "border-slate-200",
      glow: "from-slate-500/15 to-slate-300/5",
      dot: "bg-slate-400"
    },
    info: {
      border: "border-blue-200",
      glow: "from-sky-500/20 to-blue-400/5",
      dot: "bg-sky-500"
    },
    success: {
      border: "border-emerald-200",
      glow: "from-emerald-500/18 to-emerald-300/5",
      dot: "bg-emerald-500"
    },
    warning: {
      border: "border-amber-200",
      glow: "from-amber-500/18 to-amber-300/5",
      dot: "bg-amber-500"
    },
    danger: {
      border: "border-rose-200",
      glow: "from-rose-500/18 to-rose-300/5",
      dot: "bg-rose-500"
    }
  };

  return (
    <Card className={cn("relative overflow-hidden rounded-[1.4rem] bg-white p-5 shadow-[0_14px_36px_rgba(15,23,42,0.05)]", accentMap[tone].border)}>
      <div className={cn("absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r", accentMap[tone].glow)} />
      <div className="relative flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">{label}</p>
          <p className="mt-4 text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
          {hint ? <p className="mt-2 max-w-[24rem] text-sm leading-6 text-slate-600">{hint}</p> : null}
        </div>
        <span className={cn("mt-1 h-2.5 w-2.5 shrink-0 rounded-full", accentMap[tone].dot)} />
      </div>
    </Card>
  );
}
