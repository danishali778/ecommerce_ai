import * as React from "react";

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
