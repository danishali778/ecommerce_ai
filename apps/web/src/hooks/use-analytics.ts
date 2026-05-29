import { useQuery } from "@tanstack/react-query";

import { analyticsApi } from "@frontend/api-client";

export function useAnalyticsOverview(storeId: string, params: { date_from?: string; date_to?: string }) {
  return useQuery({
    queryKey: ["analytics", "overview", storeId, params.date_from ?? "", params.date_to ?? ""],
    queryFn: () => analyticsApi.getOverview(storeId, params),
    enabled: Boolean(storeId)
  });
}

export function useAnalyticsAutomation(storeId: string, params: { date_from?: string; date_to?: string }) {
  return useQuery({
    queryKey: ["analytics", "automation", storeId, params.date_from ?? "", params.date_to ?? ""],
    queryFn: () => analyticsApi.getAutomation(storeId, params),
    enabled: Boolean(storeId)
  });
}
