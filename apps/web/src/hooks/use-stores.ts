import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { storesApi } from "@frontend/api-client";

export function useDashboardSummary(selectedStoreId: string | null) {
  return useQuery({
    queryKey: ["dashboard", selectedStoreId],
    queryFn: () => storesApi.getDashboardSummary(selectedStoreId!),
    enabled: Boolean(selectedStoreId)
  });
}

export function useRunDashboardSync(selectedStoreId: string | null, onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => storesApi.createSyncRun(selectedStoreId!, "manual_full"),
    onSuccess: () => {
      if (selectedStoreId) {
        queryClient.invalidateQueries({ queryKey: ["dashboard", selectedStoreId] });
        queryClient.invalidateQueries({ queryKey: ["stores", "sync-runs", selectedStoreId] });
      }
      onSuccess?.();
    }
  });
}

export function useStoresList() {
  return useQuery({
    queryKey: ["stores"],
    queryFn: () => storesApi.list()
  });
}

export function useCreateStore(onSuccess?: (store: Awaited<ReturnType<typeof storesApi.create>>) => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; domain: string; currency: string; timezone: string }) => storesApi.create(payload),
    onSuccess: (store) => {
      queryClient.invalidateQueries({ queryKey: ["stores"] });
      queryClient.invalidateQueries({ queryKey: ["auth-me"] });
      onSuccess?.(store);
    }
  });
}

export function useStore(storeId: string) {
  return useQuery({
    queryKey: ["store", storeId],
    queryFn: () => storesApi.get(storeId),
    enabled: Boolean(storeId)
  });
}

export function useStoreIntegration(storeId: string) {
  return useQuery({
    queryKey: ["store", "integration", storeId],
    queryFn: () => storesApi.getIntegration(storeId),
    enabled: Boolean(storeId)
  });
}

export function useCreateStoreInstallUrl(storeId: string) {
  return useMutation({
    mutationFn: () => storesApi.createInstallUrl(storeId, `${window.location.origin}/shopify/callback`)
  });
}

export function useStoreSyncRuns(storeId: string) {
  return useQuery({
    queryKey: ["stores", "sync-runs", storeId],
    queryFn: () => storesApi.listSyncRuns(storeId),
    enabled: Boolean(storeId)
  });
}

export function useStoreSyncRun(storeId: string, syncRunId: string | null) {
  return useQuery({
    queryKey: ["stores", "sync-run", storeId, syncRunId],
    queryFn: () => storesApi.getSyncRun(storeId, syncRunId!),
    enabled: Boolean(storeId && syncRunId)
  });
}

export function useTriggerStoreSync(storeId: string, onSuccess?: (run: Awaited<ReturnType<typeof storesApi.createSyncRun>>) => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => storesApi.createSyncRun(storeId, "manual_full"),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: ["stores", "sync-runs", storeId] });
      onSuccess?.(run);
    }
  });
}

export function useRetryStoreSyncRun(storeId: string, onSuccess?: (run: Awaited<ReturnType<typeof storesApi.retrySyncRun>>) => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (syncRunId: string) => storesApi.retrySyncRun(storeId, syncRunId),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: ["stores", "sync-runs", storeId] });
      onSuccess?.(run);
    }
  });
}
