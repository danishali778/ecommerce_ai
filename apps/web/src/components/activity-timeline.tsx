export function ActivityTimeline({ items }: { items: Array<{ title: string; description: string; created_at: string }> }) {
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={`${item.title}-${item.created_at}`} className="relative border-l border-slate-200 pl-4">
          <span className="absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full bg-accent-500" />
          <p className="font-medium text-slate-950">{item.title}</p>
          <p className="mt-1 text-sm text-slate-600">{item.description}</p>
          <p className="mt-1 text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
}
