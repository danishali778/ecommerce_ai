import { Card } from "@frontend/ui";

export function RiskFactorCard({ title, body }: { title: string; body: string }) {
  return (
    <Card className="border-rose-100 bg-rose-50 p-4">
      <p className="font-medium text-rose-900">{title}</p>
      <p className="mt-2 text-sm text-rose-800">{body}</p>
    </Card>
  );
}
