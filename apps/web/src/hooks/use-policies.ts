import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { policiesApi } from "@frontend/api-client";

export function usePolicies(storeId: string) {
  return useQuery({
    queryKey: ["policies", storeId],
    queryFn: () => policiesApi.list(storeId),
    enabled: Boolean(storeId)
  });
}

export function useCreatePolicy(storeId: string, onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof policiesApi.create>[1]) => policiesApi.create(storeId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["policies", storeId] });
      onSuccess?.();
    }
  });
}

export function useUpdatePolicy(storeId: string, policyId: string | null, onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof policiesApi.update>[2]) => policiesApi.update(storeId, policyId!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["policies", storeId] });
      onSuccess?.();
    }
  });
}
