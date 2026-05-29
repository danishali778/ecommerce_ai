import { Card } from "@frontend/ui";

export function PolicyCitationCard({ title, body }: { title: string; body: string }) {
  return (
    <Card className="border-blue-100 bg-blue-50 p-4">
      <p className="font-medium text-blue-900">{title}</p>
      <p className="mt-2 text-sm text-blue-800">{body}</p>
    </Card>
  );
}
