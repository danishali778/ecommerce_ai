import { ProgressBar } from "@frontend/ui";

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
