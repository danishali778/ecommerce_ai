import { useMutation, useQuery } from "@tanstack/react-query";

import { catalogApi } from "@frontend/api-client";

export function useProducts(storeId: string) {
  return useQuery({
    queryKey: ["products", storeId],
    queryFn: () => catalogApi.listProducts(storeId),
    enabled: Boolean(storeId)
  });
}

export function useProduct(storeId: string, productId: string) {
  return useQuery({
    queryKey: ["product", storeId, productId],
    queryFn: () => catalogApi.getProduct(storeId, productId),
    enabled: Boolean(storeId && productId)
  });
}

export function useProductDrafts(storeId: string, productId: string) {
  return useQuery({
    queryKey: ["product-drafts", storeId, productId],
    queryFn: () => catalogApi.listDrafts(storeId, productId),
    enabled: Boolean(storeId && productId)
  });
}

export function useGenerateProductDraft(storeId: string, productId: string, onSuccess?: () => void) {
  return useMutation({
    mutationFn: () =>
      catalogApi.generateDraft(storeId, productId, {
        generation_targets: ["description", "seo", "tags"],
        tone: "clear_and_premium",
        constraints: { brand_style: "clean, modern, ecommerce-ready" }
      }),
    onSuccess
  });
}

export function useUpdateProductDraft(
  storeId: string,
  productId: string,
  draftId: string | null,
  onSuccess?: () => void
) {
  return useMutation({
    mutationFn: (payload: {
      generated_title: string | null;
      generated_description: string | null;
      generated_seo_title: string | null;
      generated_seo_description: string | null;
      generated_tags: string[];
    }) => catalogApi.updateDraft(storeId, productId, draftId!, payload),
    onSuccess
  });
}

export function useSubmitProductDraftForApproval(
  storeId: string,
  productId: string,
  draftId: string | null,
  onSuccess?: () => void
) {
  return useMutation({
    mutationFn: (approvalReason: string) => catalogApi.submitDraftForApproval(storeId, productId, draftId!, approvalReason),
    onSuccess
  });
}
