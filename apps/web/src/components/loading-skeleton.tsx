export function LoadingSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-16 animate-pulse rounded-2xl bg-slate-100" />
      ))}
    </div>
  );
}
