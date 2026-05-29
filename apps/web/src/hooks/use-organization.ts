import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { orgApi } from "@frontend/api-client";

export function useCurrentOrganization() {
  return useQuery({
    queryKey: ["organization", "current"],
    queryFn: () => orgApi.getCurrent(),
    retry: false
  });
}

export function useCreateOrganization(onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; slug: string }) => orgApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organization", "current"] });
      onSuccess?.();
    }
  });
}
