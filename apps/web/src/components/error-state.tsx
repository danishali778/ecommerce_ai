import { Button, Card } from "@frontend/ui";

export function ErrorState({ title, message, retry }: { title: string; message: string; retry?: () => void }) {
  return (
    <Card className="border-rose-200 bg-rose-50 p-6">
      <p className="text-lg font-semibold text-rose-800">{title}</p>
      <p className="mt-2 text-sm text-rose-700">{message}</p>
      {retry ? (
        <Button className="mt-4" variant="danger" onClick={retry}>
          Try Again
        </Button>
      ) : null}
    </Card>
  );
}
