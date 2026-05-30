import * as React from "react";

import { Card } from "@frontend/ui";

export function DetailPanel({
  title,
  subtitle,
  children
}: React.PropsWithChildren<{ title: string; subtitle?: string }>) {
  return (
    <Card className="motion-enter rounded-[1.5rem] border-slate-200 bg-white p-5 shadow-[0_16px_40px_rgba(15,23,42,0.05)]">
      <div className="mb-4 space-y-1">
        <h2 className="text-xl font-semibold tracking-tight text-slate-950">{title}</h2>
        {subtitle ? <p className="text-sm text-slate-600">{subtitle}</p> : null}
      </div>
      {children}
    </Card>
  );
}
