import * as React from "react";

import { Card } from "@frontend/ui";

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
