import * as React from "react";

import { Card } from "@frontend/ui";

export function SectionCard({
  title,
  actions,
  children
}: React.PropsWithChildren<{ title: string; actions?: React.ReactNode }>) {
  return (
    <Card className="motion-enter overflow-hidden rounded-[1.5rem] border-slate-200 bg-white shadow-[0_16px_40px_rgba(15,23,42,0.05)]">
      <div className="flex flex-col gap-3 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-lg font-semibold tracking-tight text-slate-950">{title}</h2>
        {actions}
      </div>
      <div className="p-5">{children}</div>
    </Card>
  );
}
