import * as React from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { catalogApi } from "@frontend/api-client";
import { Button, Card, Input, Textarea } from "@frontend/ui";

import { DraftStatusBanner, EmptyState, ErrorState, KeyValueGrid, LoadingSkeleton, MetricCard, PageHeader, SectionCard, Table } from "@/components/common";
import { formatDate, titleize } from "@/lib/format";

export function CatalogPage() {
  const { storeId = "" } = useParams();
  const productsQuery = useQuery({ queryKey: ["products", storeId], queryFn: () => catalogApi.listProducts(storeId), enabled: Boolean(storeId) });

  return (
    <div className="space-y-8">
      <PageHeader title="Catalog" description="Review synced products and open the draft workflow for individual items." />
      <SectionCard title="Products">
        {productsQuery.isLoading ? <LoadingSkeleton rows={6} /> : productsQuery.isError ? <ErrorState title="Unable to load products" message="Product data could not be loaded." retry={() => productsQuery.refetch()} /> : (productsQuery.data?.length ? (
          <Table
            headers={["Title", "Handle", "Status", "Inventory", "Updated"]}
            rows={(productsQuery.data ?? []).map((product) => [
              <Link key={product.id} className="font-medium text-accent-600" to={`/app/catalog/${storeId}/products/${product.id}`}>{product.title}</Link>,
              product.handle,
              titleize(product.status),
              String(product.inventory_total),
              formatDate(product.updated_at)
            ])}
          />
        ) : <EmptyState title="No products yet" message="Run a sync to load the store catalog." />)}
      </SectionCard>
    </div>
  );
}

export function ProductDetailPage() {
  const { storeId = "", productId = "" } = useParams();
  const queryClient = useQueryClient();
  const productQuery = useQuery({ queryKey: ["product", storeId, productId], queryFn: () => catalogApi.getProduct(storeId, productId), enabled: Boolean(storeId && productId) });
  const draftsQuery = useQuery({ queryKey: ["product-drafts", storeId, productId], queryFn: () => catalogApi.listDrafts(storeId, productId), enabled: Boolean(storeId && productId) });
  const [draftForm, setDraftForm] = React.useState({ generated_title: "", generated_description: "", generated_seo_title: "", generated_seo_description: "", generated_tags: "" });
  const [approvalReason, setApprovalReason] = React.useState("Draft is ready for review.");

  const activeDraft = draftsQuery.data?.[0] ?? productQuery.data?.latest_draft ?? null;

  React.useEffect(() => {
    if (!activeDraft) return;
    setDraftForm({
      generated_title: activeDraft.generated_title ?? "",
      generated_description: activeDraft.generated_description ?? "",
      generated_seo_title: activeDraft.generated_seo_title ?? "",
      generated_seo_description: activeDraft.generated_seo_description ?? "",
      generated_tags: (activeDraft.generated_tags ?? []).join(", ")
    });
  }, [activeDraft]);

  const generateMutation = useMutation({
    mutationFn: () =>
      catalogApi.generateDraft(storeId, productId, {
        generation_targets: ["description", "seo", "tags"],
        tone: "clear_and_premium",
        constraints: { brand_style: "clean, modern, ecommerce-ready" }
      }),
    onSuccess: () => draftsQuery.refetch()
  });
  const updateMutation = useMutation({
    mutationFn: () =>
      catalogApi.updateDraft(storeId, productId, activeDraft!.id, {
        generated_title: draftForm.generated_title || null,
        generated_description: draftForm.generated_description || null,
        generated_seo_title: draftForm.generated_seo_title || null,
        generated_seo_description: draftForm.generated_seo_description || null,
        generated_tags: draftForm.generated_tags.split(",").map((item) => item.trim()).filter(Boolean)
      }),
    onSuccess: () => {
      draftsQuery.refetch();
      productQuery.refetch();
    }
  });
  const submitApprovalMutation = useMutation({
    mutationFn: () => catalogApi.submitDraftForApproval(storeId, productId, activeDraft!.id, approvalReason),
    onSuccess: () => {
      draftsQuery.refetch();
      productQuery.refetch();
    }
  });

  if (productQuery.isLoading) return <LoadingSkeleton rows={6} />;
  if (productQuery.isError) return <ErrorState title="Unable to load product" message="The selected product could not be loaded." retry={() => productQuery.refetch()} />;

  const product = productQuery.data!;

  return (
    <div className="space-y-8">
      <PageHeader title={product.title} description="Review live product context, generate draft content, and submit the draft for approval." />
      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <MetricCard label="Inventory" value={product.inventory_total} />
            <MetricCard label="Status" value={titleize(product.status)} />
            <MetricCard label="Vendor" value={product.vendor ?? "—"} />
            <MetricCard label="Variants" value={product.variants.length} />
          </div>
          <SectionCard title="Live Product Context">
            <KeyValueGrid
              items={[
                { label: "Handle", value: product.handle },
                { label: "SEO Title", value: product.seo_title ?? "—" },
                { label: "Updated", value: formatDate(product.updated_at) },
                { label: "Primary Variant", value: product.variants[0]?.title ?? "—" }
              ]}
            />
          </SectionCard>
          <SectionCard title="Variants">
            <Table
              headers={["Title", "SKU", "Price", "Inventory"]}
              rows={product.variants.map((variant) => [variant.title, variant.sku ?? "—", variant.price, String(variant.inventory_quantity)])}
            />
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="AI Suggested Optimization"
            actions={
              <div className="flex gap-3">
                <Button variant="secondary" onClick={() => generateMutation.mutate()}>
                  {generateMutation.isPending ? "Generating..." : "Regenerate"}
                </Button>
                {activeDraft ? (
                  <Button onClick={() => updateMutation.mutate()} disabled={updateMutation.isPending}>
                    Save Draft
                  </Button>
                ) : (
                  <Button onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
                    Generate Draft
                  </Button>
                )}
              </div>
            }
          >
            {activeDraft ? (
              <div className="space-y-4">
                <DraftStatusBanner status={activeDraft.status} modelName={activeDraft.model_name} />
                <Input placeholder="Generated title" value={draftForm.generated_title} onChange={(event) => setDraftForm((current) => ({ ...current, generated_title: event.target.value }))} />
                <Textarea placeholder="Generated description" value={draftForm.generated_description} onChange={(event) => setDraftForm((current) => ({ ...current, generated_description: event.target.value }))} />
                <Input placeholder="Generated SEO title" value={draftForm.generated_seo_title} onChange={(event) => setDraftForm((current) => ({ ...current, generated_seo_title: event.target.value }))} />
                <Textarea placeholder="Generated SEO description" value={draftForm.generated_seo_description} onChange={(event) => setDraftForm((current) => ({ ...current, generated_seo_description: event.target.value }))} />
                <Input placeholder="tag-one, tag-two" value={draftForm.generated_tags} onChange={(event) => setDraftForm((current) => ({ ...current, generated_tags: event.target.value }))} />
                <Card className="p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Approval submission reason</p>
                  <Textarea className="mt-3" value={approvalReason} onChange={(event) => setApprovalReason(event.target.value)} />
                </Card>
                <Button className="w-full" onClick={() => submitApprovalMutation.mutate()} disabled={submitApprovalMutation.isPending}>
                  {submitApprovalMutation.isPending ? "Submitting..." : "Submit for Approval"}
                </Button>
                {submitApprovalMutation.data ? (
                  <p className="text-sm text-emerald-700">Submitted. Approval ID: {submitApprovalMutation.data.approval_id}</p>
                ) : null}
              </div>
            ) : (
              <EmptyState title="No draft yet" message="Generate a product draft to start the review workflow." action={<Button onClick={() => generateMutation.mutate()}>Generate Draft</Button>} />
            )}
          </SectionCard>
          {activeDraft ? (
            <SectionCard title="Draft Metadata">
              <KeyValueGrid
                items={[
                  { label: "Created", value: formatDate(activeDraft.created_at) },
                  { label: "Updated", value: formatDate(activeDraft.updated_at) },
                  { label: "Model", value: activeDraft.model_name },
                  { label: "Status", value: titleize(activeDraft.status) }
                ]}
              />
            </SectionCard>
          ) : null}
        </div>
      </div>
    </div>
  );
}
