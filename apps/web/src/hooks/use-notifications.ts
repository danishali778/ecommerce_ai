import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { notificationsApi } from "@frontend/api-client";

export function useNotifications(status?: string) {
  return useQuery({
    queryKey: ["notifications", status ?? ""],
    queryFn: () => notificationsApi.list({ status: status || undefined })
  });
}

export function useMarkNotificationRead(onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) => notificationsApi.markRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      onSuccess?.();
    }
  });
}
