import { useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { AlertTriangle, ArrowRight, CirclePause, Search, ShieldCheck, ShieldX } from "lucide-react";

import { Button, Card, Input, Textarea } from "@frontend/ui";
import {
  DetailPanel,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
  MetricCard,
  PageHeader,
  ReviewRequiredBanner,
  RiskFactorCard,
  SectionCard,
  StatusPill
} from "@/components/common";
import { useFraudOrder, useFraudReview, useFraudReviews, useRecordFraudDecision } from "@/hooks/use-fraud";
import { formatDate, titleize } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function toneForRisk(score: number) {
  if (score >= 85) return "danger";
  if (score >= 60) return "warning";
  return "info";
}

function riskSummary(reason: string) {
  const normalized = reason.toLowerCase();
  if (normalized.includes("ip")) return "Network and destination data look inconsistent with the order profile.";
  if (normalized.includes("email")) return "Email identity patterns resemble prior suspicious checkout behavior.";
  if (normalized.includes("value")) return "Order value is materially outside the store baseline and requires a human check.";
  if (normalized.includes("attempt")) return "Repeated payment attempts raise the likelihood of abusive checkout behavior.";
  return "This factor contributed to the review being surfaced for manual fraud inspection.";
}

function DecisionBar({
  onDecision,
  pending
}: {
  onDecision: (decision: "approved" | "held" | "rejected", notes?: string) => void;
  pending: boolean;
}) {
  const [notes, setNotes] = useState("");

  return (
    <div className="space-y-4">
      <Textarea
        rows={4}
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
        placeholder="Decision notes for the fraud review..."
      />
      <div className="flex flex-wrap gap-3">
        <Button disabled={pending} onClick={() => onDecision("approved", notes)}>
          <ShieldCheck className="mr-2 h-4 w-4" />
          Approve Order
        </Button>
        <Button variant="secondary" disabled={pending} onClick={() => onDecision("held", notes)}>
          <CirclePause className="mr-2 h-4 w-4" />
          Hold for Review
        </Button>
        <Button variant="danger" disabled={pending} onClick={() => onDecision("rejected", notes)}>
          <ShieldX className="mr-2 h-4 w-4" />
          Reject / Escalate
        </Button>
      </div>
    </div>
  );
}

export function FraudPage() {
  const { storeId = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [riskFilter, setRiskFilter] = useState("");
  const [search, setSearch] = useState("");

  const reviewsQuery = useFraudReviews(storeId, riskFilter || undefined);

  const reviews = reviewsQuery.data ?? [];
  const selectedId = searchParams.get("review") ?? reviews[0]?.id ?? "";
  const selected = reviews.find((review) => review.id === selectedId) ?? null;
  const filteredReviews = reviews.filter((review) => {
    const statusMatches = riskFilter ? review.risk_status.toLowerCase().includes(riskFilter.toLowerCase()) : true;
    const searchMatches = search
      ? [review.id, review.order_id, review.risk_status, review.reason_codes_json.join(" ")]
          .join(" ")
          .toLowerCase()
          .includes(search.toLowerCase())
      : true;
    return statusMatches && searchMatches;
  });

  const highRiskCount = reviews.filter((review) => review.risk_score >= 80).length;
  const pendingCount = reviews.filter((review) => !review.decision).length;
  const reviewedCount = reviews.filter((review) => Boolean(review.decision)).length;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Fraud review queue"
        description="Review surfaced high-risk orders, inspect evidence, and record internal decisions without mutating Shopify directly."
        actions={
          <div className="flex flex-wrap gap-3">
            <div className="relative min-w-56">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search order or risk factor" />
            </div>
            <Input value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)} placeholder="Filter by risk status" />
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="High Risk" value={highRiskCount} hint="Reviews at or above the critical range" tone={highRiskCount ? "danger" : "success"} />
        <MetricCard label="Pending Review" value={pendingCount} hint="Cases still awaiting a human decision" tone={pendingCount ? "warning" : "success"} />
        <MetricCard label="Reviewed" value={reviewedCount} hint="Decisions already recorded for this store" tone="info" />
      </div>

      {reviewsQuery.isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : reviewsQuery.isError ? (
        <ErrorState title="Could not load fraud reviews" message={messageFromError(reviewsQuery.error)} />
      ) : filteredReviews.length === 0 ? (
        <EmptyState
          title="No risk reviews yet"
          message="Orders are being scored, but none have crossed the risk threshold required for manual review."
        />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[0.78fr_1.22fr]">
          <SectionCard title="Review queue">
            <div className="space-y-3">
              {filteredReviews.map((review) => (
                <button
                  key={review.id}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    review.id === selectedId ? "border-accent-300 bg-accent-50" : "border-slate-200 bg-white hover:border-accent-200"
                  }`}
                  onClick={() => setSearchParams({ review: review.id })}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-slate-950">{review.order_id}</p>
                        <StatusPill value={review.decision ?? "pending"} />
                      </div>
                      <p className="text-sm text-slate-600">
                        Risk score {review.risk_score} - {titleize(review.risk_status)}
                      </p>
                      <p className="text-xs text-slate-500">{formatDate(review.created_at)}</p>
                    </div>
                    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
                      review.risk_score >= 85 ? "bg-rose-50 text-rose-700" : review.risk_score >= 60 ? "bg-amber-50 text-amber-700" : "bg-blue-50 text-blue-700"
                    }`}>
                      {review.risk_score}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </SectionCard>

          {selected ? (
            <div className="space-y-6">
              <DetailPanel title={`Order ${selected.order_id}`} subtitle="Selected review preview">
                <KeyValueGrid
                  items={[
                    { label: "Risk status", value: <StatusPill value={selected.risk_status} /> },
                    { label: "Risk score", value: selected.risk_score },
                    { label: "Decision", value: selected.decision ? <StatusPill value={selected.decision} /> : "Pending" },
                    { label: "Created", value: formatDate(selected.created_at) }
                  ]}
                />
              </DetailPanel>

              <SectionCard title="Decision support">
                <div className="space-y-4">
                  <ReviewRequiredBanner message="CommerceOps provides evidence and structured reasoning. Final outcomes remain human-recorded internal decisions." />
                  <div className="grid gap-3 md:grid-cols-2">
                    {selected.reason_codes_json.map((reason) => (
                      <RiskFactorCard key={reason} title={titleize(reason)} body={riskSummary(reason)} />
                    ))}
                  </div>
                </div>
              </SectionCard>

              <Card className="p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Open full review</p>
                    <p className="mt-1 text-sm text-slate-600">Inspect order detail, current decision state, and capture reviewer notes.</p>
                  </div>
                  <Link to={`/app/fraud/${storeId}/reviews/${selected.id}`}>
                    <Button>
                      Review Workspace
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </Card>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

export function FraudDetailPage() {
  const { storeId = "", riskReviewId = "" } = useParams();
  const reviewQuery = useFraudReview(storeId, riskReviewId);

  const review = reviewQuery.data;

  const orderQuery = useFraudOrder(storeId, review?.order_id);

  const recordDecision = useRecordFraudDecision(storeId, riskReviewId);

  if (reviewQuery.isLoading) return <LoadingSkeleton rows={6} />;
  if (reviewQuery.isError || !review) {
    return <ErrorState title="Could not load fraud review" message={messageFromError(reviewQuery.error)} />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title={`Fraud review ${review.id}`}
        description="Inspect evidence, review current state, and record the final internal decision for the surfaced order."
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-6">
          <Card className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className={`inline-flex h-10 w-10 items-center justify-center rounded-2xl ${
                    review.risk_score >= 85 ? "bg-rose-50 text-rose-700" : "bg-amber-50 text-amber-700"
                  }`}>
                    <AlertTriangle className="h-4 w-4" />
                  </span>
                  <div>
                    <p className="text-xl font-semibold text-slate-950">{orderQuery.data?.external_order_id ?? review.order_id}</p>
                    <p className="text-sm text-slate-600">Decision support for high-risk order review</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <StatusPill value={review.risk_status} />
                  <StatusPill value={review.decision ?? "pending"} />
                </div>
              </div>
              <div className={`rounded-2xl border px-4 py-3 text-center ${
                review.risk_score >= 85 ? "border-rose-200 bg-rose-50" : "border-amber-200 bg-amber-50"
              }`}>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Risk score</p>
                <p className="mt-2 text-3xl font-semibold text-slate-950">{review.risk_score}</p>
              </div>
            </div>
          </Card>

          <DetailPanel title="Order summary" subtitle="Ground the decision in the order record currently in the workspace">
            <KeyValueGrid
              items={[
                { label: "Order total", value: orderQuery.data ? `${orderQuery.data.total} ${orderQuery.data.currency ?? ""}` : "Loading..." },
                { label: "Payment status", value: orderQuery.data?.payment_status ?? "Unknown" },
                { label: "Fulfillment status", value: orderQuery.data?.fulfillment_status ?? "Unknown" },
                { label: "Created", value: formatDate(review.created_at) }
              ]}
            />
          </DetailPanel>

          <SectionCard title="Record decision">
            <div className="space-y-4">
              <ReviewRequiredBanner message="Record only internal review decisions here. CommerceOps does not directly cancel, refund, or mutate Shopify orders from this screen." />
              <DecisionBar
                pending={recordDecision.isPending}
                onDecision={(decision, notes) => recordDecision.mutate({ decision, reason: notes ?? "" })}
              />
              {recordDecision.isError ? (
                <p className="text-sm text-rose-700">{messageFromError(recordDecision.error)}</p>
              ) : null}
            </div>
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard title="Identified risk factors">
            <div className="space-y-3">
              {review.reason_codes_json.map((reason) => (
                <RiskFactorCard key={reason} title={titleize(reason)} body={riskSummary(reason)} />
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Current review state">
            <KeyValueGrid
              items={[
                { label: "Decision", value: review.decision ? <StatusPill value={review.decision} /> : "Pending" },
                { label: "Reviewed by", value: review.reviewed_by_user_id ?? "Unassigned" },
                { label: "Reviewed at", value: review.reviewed_at ? formatDate(review.reviewed_at) : "Not reviewed yet" },
                { label: "Notes", value: review.decision_notes ?? "No notes yet" }
              ]}
            />
          </SectionCard>

          <Card className="border-slate-200 bg-slate-50 p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Decision support only</p>
            <p className="mt-3 text-sm leading-7 text-slate-700">
              Fraud factors shown here are evidence for human judgment. CommerceOps helps operators review suspicious orders, but does not take direct Shopify-side enforcement actions from this workspace.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
