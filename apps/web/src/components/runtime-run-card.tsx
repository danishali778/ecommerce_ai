import * as React from "react";

import { Card } from "@frontend/ui";

import { StatusPill } from "@/components/status-pill";

export function RuntimeRunCard({
  title,
  status,
  meta,
  body
}: {
  title: string;
  status: string;
  meta?: string;
  body?: React.ReactNode;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-950">{title}</p>
          {meta ? <p className="mt-1 text-sm text-slate-600">{meta}</p> : null}
        </div>
        <StatusPill value={status} />
      </div>
      {body ? <div className="mt-4 text-sm text-slate-700">{body}</div> : null}
    </Card>
  );
}
