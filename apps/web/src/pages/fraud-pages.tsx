import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { catalogApi, fraudApi } from "@frontend/api-client";
import { Button, Card, Input, Textarea } from "@frontend/ui";
import {
  DetailPanel,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
  PageHeader,
  RiskFactorCard,
  SectionCard,
  StatusPill
} from "@/components/common";
import { formatDate } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
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
      <Textarea rows={4} value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Decision notes for the fraud review..." />
      <div className="flex flex-wrap gap-3">
        <Button disabled={pending} onClick={() => onDecision("approved", notes)}>
          Approve order
        </Button>
        <Button variant="secondary" disabled={pending} onClick={() => onDecision("held", notes)}>
          Hold for review
        </Button>
        <Button variant="danger" disabled={pending} onClick={() => onDecision("rejected", notes)}>
          Reject / escalate
        </Button>
      </div>
    </div>
  );
}

export function FraudPage() {
  const { storeId = "" } = useParams();
  const [riskFilter, setRiskFilter] = useState("");

  const reviewsQuery = useQuery({
    queryKey: ["fraud", "reviews", storeId, riskFilter],
    queryFn: () => fraudApi.listRiskReviews(storeId, riskFilter || undefined),
    enabled: Boolean(storeId)
  });

  const reviews = reviewsQuery.data ?? [];
  const selected = reviews[0];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Fraud review queue"
        description="Review high-risk orders, inspect risk factors, and record internal decisions without mutating Shopify directly."
        actions={
          <div className="flex items-center gap-3">
            <Input value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)} placeholder="Filter by risk status" />
          </div>
        }
      />

      {reviewsQuery.isLoading ? (
        <LoadingSkeleton rows={5} />
      ) : reviewsQuery.isError ? (
        <ErrorState title="Could not load fraud reviews" message={messageFromError(reviewsQuery.error)} />
      ) : reviews.length === 0 ? (
        <EmptyState
          title="No risk reviews yet"
          message="Orders are being scored, but none have crossed the risk threshold required for a manual review."
        />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
          <SectionCard title="Review queue">
            <div className="space-y-3">
              {reviews.map((review) => (
                <a
                  key={review.id}
                  href={`/app/fraud/${storeId}/reviews/${review.id}`}
                  className="block rounded-2xl border border-slate-200 p-4 transition hover:border-accent-300 hover:bg-accent-50"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-950">{review.order_id}</p>
                      <p className="mt-1 text-sm text-slate-600">
                        Score {review.risk_score} · Created {formatDate(review.created_at)}
                      </p>
                    </div>
                    <StatusPill value={review.risk_status} />
                  </div>
                </a>
              ))}
            </div>
          </SectionCard>

          {selected ? (
            <DetailPanel title="Selected review" subtitle="Open a review to inspect evidence and record a decision.">
              <KeyValueGrid
                items={[
                  { label: "Review ID", value: selected.id },
                  { label: "Order", value: selected.order_id },
                  { label: "Risk score", value: selected.risk_score },
                  { label: "Decision", value: selected.decision ? <StatusPill value={selected.decision} /> : "Pending" }
                ]}
              />
              <div className="mt-4 text-sm text-slate-600">
                Use the queue to open a specific review and capture the final human decision.
              </div>
            </DetailPanel>
          ) : null}
        </div>
      )}
    </div>
  );
}

export function FraudDetailPage() {
  const { storeId = "", riskReviewId = "" } = useParams();
  const queryClient = useQueryClient();

  const reviewQuery = useQuery({
    queryKey: ["fraud", "review", storeId, riskReviewId],
    queryFn: () => fraudApi.getRiskReview(storeId, riskReviewId),
    enabled: Boolean(storeId && riskReviewId)
  });

  const review = reviewQuery.data;

  const orderQuery = useQuery({
    queryKey: ["fraud", "order", storeId, review?.order_id],
    queryFn: () => catalogApi.getOrder(storeId, review!.order_id),
    enabled: Boolean(storeId && review?.order_id)
  });

  const recordDecision = useMutation({
    mutationFn: ({ decision, notes }: { decision: "approved" | "held" | "rejected"; notes?: string }) =>
      fraudApi.recordDecision(storeId, riskReviewId, decision, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fraud", "review", storeId, riskReviewId] });
      queryClient.invalidateQueries({ queryKey: ["fraud", "reviews", storeId] });
    }
  });

  if (reviewQuery.isLoading) return <LoadingSkeleton rows={6} />;
  if (reviewQuery.isError || !review) {
    return <ErrorState title="Could not load fraud review" message={messageFromError(reviewQuery.error)} />;
  }

  return (
    <div className="space-y-8">
      <PageHeader title={`Fraud review ${review.id}`} description="Decision support for high-risk orders." />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-6">
          <DetailPanel title={`Order ${orderQuery.data?.external_order_id ?? review.order_id}`} subtitle="Selected order summary">
            <KeyValueGrid
              items={[
                { label: "Risk status", value: <StatusPill value={review.risk_status} /> },
                { label: "Risk score", value: review.risk_score },
                { label: "Order total", value: orderQuery.data ? `${orderQuery.data.total} ${orderQuery.data.currency ?? ""}` : "Loading..." },
                { label: "Created", value: formatDate(review.created_at) }
              ]}
            />
          </DetailPanel>

          <SectionCard title="Decision support">
            <p className="text-sm leading-7 text-slate-700">
              CommerceOps surfaces risk factors and capture signals, but the final outcome is still a human-recorded internal decision.
            </p>
          </SectionCard>

          <SectionCard title="Record decision">
            <DecisionBar
              pending={recordDecision.isPending}
              onDecision={(decision, notes) => recordDecision.mutate({ decision, notes })}
            />
            {recordDecision.isError ? (
              <p className="mt-3 text-sm text-rose-700">{messageFromError(recordDecision.error)}</p>
            ) : null}
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard title="Identified risk factors">
            <div className="space-y-3">
              {review.reason_codes_json.map((reason) => (
                <RiskFactorCard
                  key={reason}
                  title={reason.replaceAll("_", " ")}
                  body="This signal contributed to the review being surfaced for human inspection."
                />
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Current decision state">
            <KeyValueGrid
              items={[
                { label: "Decision", value: review.decision ? <StatusPill value={review.decision} /> : "Pending" },
                { label: "Reviewed by", value: review.reviewed_by_user_id ?? "Unassigned" },
                { label: "Reviewed at", value: review.reviewed_at ? formatDate(review.reviewed_at) : "Not reviewed yet" },
                { label: "Notes", value: review.decision_notes ?? "No notes yet" }
              ]}
            />
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
