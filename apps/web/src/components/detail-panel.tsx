import * as React from "react";

import { Card } from "@frontend/ui";

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
