import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { catalogApi, fraudApi } from "@frontend/api-client";

export function useFraudReviews(storeId: string, riskStatus?: string) {
  return useQuery({
    queryKey: ["fraud", "reviews", storeId, riskStatus ?? ""],
    queryFn: () => fraudApi.listRiskReviews(storeId, riskStatus || undefined),
    enabled: Boolean(storeId)
  });
}

export function useFraudReview(storeId: string, riskReviewId: string) {
  return useQuery({
    queryKey: ["fraud", "review", storeId, riskReviewId],
    queryFn: () => fraudApi.getRiskReview(storeId, riskReviewId),
    enabled: Boolean(storeId && riskReviewId)
  });
}

export function useFraudOrder(storeId: string, orderId: string | null | undefined) {
  return useQuery({
    queryKey: ["fraud", "order", storeId, orderId],
    queryFn: () => catalogApi.getOrder(storeId, orderId!),
    enabled: Boolean(storeId && orderId)
  });
}

export function useRecordFraudDecision(storeId: string, riskReviewId: string, onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ decision, reason }: { decision: "approved" | "held" | "rejected"; reason: string }) =>
      fraudApi.recordDecision(storeId, riskReviewId, decision, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fraud", "reviews", storeId] });
      queryClient.invalidateQueries({ queryKey: ["fraud", "review", storeId, riskReviewId] });
      onSuccess?.();
    }
  });
}
