import * as React from "react";

export function PageHeader({
  title,
  description,
  actions
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="border-b border-slate-200 pb-8 pt-2 motion-enter">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-end">
        <div className="min-w-0">
          <div className="mb-4 flex items-center gap-3">
            <div className="h-px w-12 bg-accent-500" />
            <p className="section-kicker text-accent-700">Operations workspace</p>
          </div>
          <div className="space-y-3">
            <span className="eyebrow">Live overview</span>
            <h1 className="section-title max-w-4xl">{title}</h1>
            {description ? <p className="section-copy max-w-3xl text-base leading-8 text-slate-600">{description}</p> : null}
          </div>
        </div>
        {actions ? <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap xl:justify-end">{actions}</div> : null}
      </div>
      <div className="mt-7 flex items-center gap-3">
        <span className="h-2 w-2 rounded-full bg-accent-500" />
        <div className="divider-gradient" />
      </div>
    </div>
  );
}
