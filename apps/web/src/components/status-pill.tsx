import { Badge } from "@frontend/ui";

export function StatusPill({ value }: { value: string }) {
  const normalized = value.toLowerCase();
  const tone =
    normalized.includes("success") || normalized.includes("ready") || normalized.includes("approved") || normalized.includes("resolved")
      ? "success"
      : normalized.includes("fail") || normalized.includes("rejected") || normalized.includes("critical")
        ? "danger"
        : normalized.includes("review") || normalized.includes("pending") || normalized.includes("queue")
          ? "warning"
          : "info";
  return <Badge tone={tone}>{value.replaceAll("_", " ")}</Badge>;
}
