import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { inventoryApi } from "@frontend/api-client";

export function useInventoryAlerts(storeId: string, status?: string) {
  return useQuery({
    queryKey: ["inventory", "alerts", storeId, status ?? ""],
    queryFn: () => inventoryApi.listAlerts(storeId, status || undefined),
    enabled: Boolean(storeId)
  });
}

export function useReorderSuggestions(storeId: string, status?: string) {
  return useQuery({
    queryKey: ["inventory", "suggestions", storeId, status ?? ""],
    queryFn: () => inventoryApi.listSuggestions(storeId, status || undefined),
    enabled: Boolean(storeId)
  });
}

export function useSaveSupplierDraft(storeId: string, suggestionId: string | null, onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof inventoryApi.createOrRefreshSupplierDraft>[2]) =>
      inventoryApi.createOrRefreshSupplierDraft(storeId, suggestionId!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory", "suggestions", storeId] });
      onSuccess?.();
    }
  });
}
