import { Card } from "@frontend/ui";

export function SupplierDraftCard({ subject, body }: { subject: string; body: string }) {
  return (
    <Card className="p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Supplier Draft</p>
      <p className="mt-2 font-medium text-slate-900">{subject}</p>
      <pre className="mt-3 whitespace-pre-wrap text-sm text-slate-700">{body}</pre>
    </Card>
  );
}
