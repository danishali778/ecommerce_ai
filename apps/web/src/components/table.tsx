import * as React from "react";

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
