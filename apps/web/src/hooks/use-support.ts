import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { catalogApi, supportApi } from "@frontend/api-client";

export function useSupportConversations(storeId: string, status?: string) {
  return useQuery({
    queryKey: ["support", "conversations", storeId, status ?? ""],
    queryFn: () => supportApi.listConversations(storeId, status || undefined),
    enabled: Boolean(storeId)
  });
}

export function useSupportCustomers(storeId: string) {
  return useQuery({
    queryKey: ["support", "customers", storeId],
    queryFn: () => catalogApi.listCustomers(storeId),
    enabled: Boolean(storeId)
  });
}

export function useSupportOrders(storeId: string) {
  return useQuery({
    queryKey: ["support", "orders", storeId],
    queryFn: () => catalogApi.listOrders(storeId),
    enabled: Boolean(storeId)
  });
}

export function useCreateSupportConversation(storeId: string, onSuccess?: (conversation: Awaited<ReturnType<typeof supportApi.createConversation>>) => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof supportApi.createConversation>[1]) => supportApi.createConversation(storeId, payload),
    onSuccess: (conversation) => {
      queryClient.invalidateQueries({ queryKey: ["support", "conversations", storeId] });
      onSuccess?.(conversation);
    }
  });
}

export function useSupportConversation(storeId: string, conversationId: string) {
  return useQuery({
    queryKey: ["support", "conversation", storeId, conversationId],
    queryFn: () => supportApi.getConversation(storeId, conversationId),
    enabled: Boolean(storeId && conversationId)
  });
}

export function useSupportMessages(storeId: string, conversationId: string) {
  return useQuery({
    queryKey: ["support", "messages", storeId, conversationId],
    queryFn: () => supportApi.listMessages(storeId, conversationId),
    enabled: Boolean(storeId && conversationId)
  });
}

export function useSupportCustomer(storeId: string, customerId: string | null | undefined) {
  return useQuery({
    queryKey: ["support", "customer", storeId, customerId],
    queryFn: () => catalogApi.getCustomer(storeId, customerId!),
    enabled: Boolean(storeId && customerId)
  });
}

export function useSupportOrder(storeId: string, orderId: string | null | undefined) {
  return useQuery({
    queryKey: ["support", "order", storeId, orderId],
    queryFn: () => catalogApi.getOrder(storeId, orderId!),
    enabled: Boolean(storeId && orderId)
  });
}

export function useAddSupportMessage(storeId: string, conversationId: string, onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof supportApi.createMessage>[2]) => supportApi.createMessage(storeId, conversationId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["support", "messages", storeId, conversationId] });
      queryClient.invalidateQueries({ queryKey: ["support", "conversations", storeId] });
      onSuccess?.();
    }
  });
}

export function useUpdateSupportConversation(storeId: string, conversationId: string, onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (status: Parameters<typeof supportApi.updateConversation>[2]) => supportApi.updateConversation(storeId, conversationId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["support", "conversations", storeId] });
      queryClient.invalidateQueries({ queryKey: ["support", "conversation", storeId, conversationId] });
      onSuccess?.();
    }
  });
}

export function useGenerateSupportDraft(storeId: string, conversationId: string, onSuccess?: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => supportApi.generateDraft(storeId, conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["support", "messages", storeId, conversationId] });
      queryClient.invalidateQueries({ queryKey: ["support", "conversations", storeId] });
      queryClient.invalidateQueries({ queryKey: ["support", "conversation", storeId, conversationId] });
      onSuccess?.();
    }
  });
}
