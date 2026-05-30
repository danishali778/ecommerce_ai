export function ActivityTimeline({ items }: { items: Array<{ title: string; description: string; created_at: string }> }) {
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={`${item.title}-${item.created_at}`} className="relative rounded-[1.45rem] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.9),rgba(248,250,252,0.94))] p-4 pl-6">
          <span className="absolute bottom-4 left-[1.45rem] top-4 w-px bg-slate-200" />
          <span className="absolute left-3 top-5 h-4 w-4 rounded-full border-4 border-white bg-accent-500 shadow-sm" />
          <div className="pl-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className="font-medium text-slate-950">{item.title}</p>
              <span className="w-fit rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-slate-500 shadow-sm">
                {new Date(item.created_at).toLocaleString()}
              </span>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
