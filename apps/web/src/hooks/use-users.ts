import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { usersApi } from "@frontend/api-client";

export function useRoles() {
  return useQuery({
    queryKey: ["users", "roles"],
    queryFn: () => usersApi.listRoles()
  });
}

export function useUsers(search?: string, role?: string) {
  return useQuery({
    queryKey: ["users", "list", search ?? "", role ?? ""],
    queryFn: () => usersApi.list({ q: search || undefined, role: role || undefined })
  });
}

export function useCreateUser(onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof usersApi.create>[0]) => usersApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "list"] });
      onSuccess?.();
    }
  });
}

export function useUpdateUser(userId: string, onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof usersApi.update>[1]) => usersApi.update(userId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", "list"] });
      onSuccess?.();
    }
  });
}
