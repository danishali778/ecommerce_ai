import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { approvalsApi } from "@frontend/api-client";

export function useApprovals() {
  return useQuery({ queryKey: ["approvals"], queryFn: () => approvalsApi.list() });
}

export function useApproval(approvalId: string) {
  return useQuery({
    queryKey: ["approval", approvalId],
    queryFn: () => approvalsApi.get(approvalId),
    enabled: Boolean(approvalId)
  });
}

export function useApprovalActions(onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      action,
      approvalIds,
      notes
    }: {
      action: "approve" | "reject" | "cancel" | "retry";
      approvalIds: string[];
      notes: string;
    }) => {
      await Promise.all(
        approvalIds.map((approvalId) => {
          if (action === "approve") return approvalsApi.approve(approvalId, notes);
          if (action === "reject") return approvalsApi.reject(approvalId, notes);
          if (action === "cancel") return approvalsApi.cancel(approvalId, notes);
          return approvalsApi.retryExecution(approvalId, notes);
        })
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
      onSuccess?.();
    }
  });
}
