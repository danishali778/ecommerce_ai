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
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div className="space-y-1">
        <h1 className="section-title">{title}</h1>
        {description ? <p className="section-copy max-w-3xl">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
    </div>
  );
}
