import * as React from "react";

import { Card } from "@frontend/ui";

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
