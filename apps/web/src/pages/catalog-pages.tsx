import * as React from "react";
import { Link, useParams } from "react-router-dom";
import { Button, Card, Input, Textarea } from "@frontend/ui";
import { ArrowUpRight, Boxes, Package2, Sparkles, Tag } from "lucide-react";

import { DraftStatusBanner, EmptyState, ErrorState, KeyValueGrid, LoadingSkeleton, PageHeader, SectionCard } from "@/components/common";
import {
  useGenerateProductDraft,
  useProduct,
  useProductDrafts,
  useProducts,
  useSubmitProductDraftForApproval,
  useUpdateProductDraft
} from "@/hooks/use-catalog";
import { formatDate, titleize } from "@/lib/format";

function ProductStatusTone(status: string) {
  const normalized = status.toLowerCase();
  if (normalized.includes("active")) return "success";
  if (normalized.includes("draft")) return "warning";
  if (normalized.includes("archived")) return "danger";
  return "neutral";
}

function ProductStatusBadge({ status }: { status: string }) {
  const tone = ProductStatusTone(status);
  const classes =
    tone === "success"
      ? "border border-emerald-200 bg-emerald-50 text-emerald-700"
      : tone === "warning"
        ? "border border-amber-200 bg-amber-50 text-amber-700"
        : tone === "danger"
          ? "border border-rose-200 bg-rose-50 text-rose-700"
          : "border border-slate-200 bg-white text-slate-600";

  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${classes}`}>{titleize(status)}</span>;
}

function formatCatalogState(product: { inventory_total: number; status: string }) {
  if (product.inventory_total <= 0) return "Needs inventory attention";
  if (product.status === "draft") return "Draft product in catalog";
  if (product.status === "archived") return "Archived product record";
  return "Live product record";
}

function formatVendorName(vendor: string | null | undefined) {
  if (!vendor) return "Unknown";
  return titleize(vendor.replace(/[_-]+/g, " "));
}

function normalizeGeneratedDescription(value: string | null | undefined) {
  if (!value) return "";
  const trimmed = value.trim();
  if (!(trimmed.startsWith("[") && trimmed.endsWith("]"))) return value;

  const inner = trimmed.slice(1, -1).trim();
  if (!inner) return "";

  const parts = inner
    .split(/['"]\s*,\s*['"]/)
    .map((part) => part.replace(/^['"\s]+|['"\s]+$/g, "").trim())
    .filter(Boolean);

  return parts.length ? parts.join("\n\n") : value;
}

function formatVariantRecordLabel(externalVariantId: string | null | undefined) {
  if (!externalVariantId) return "No linked channel record";
  if (externalVariantId.startsWith("gid://")) return "Linked Shopify variant";
  return externalVariantId;
}

export function CatalogPage() {
  const { storeId = "" } = useParams();
  const productsQuery = useProducts(storeId);

  const products = productsQuery.data ?? [];
  const activeProducts = products.filter((product) => product.status === "active").length;
  const draftProducts = products.filter((product) => product.status === "draft").length;
  const zeroInventoryProducts = products.filter((product) => product.inventory_total <= 0).length;

  return (
    <div className="space-y-8">
      <PageHeader title="Catalog" description="Review synced products and open the draft workflow for individual items." />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(21rem,0.92fr)]">
        <SectionCard title="Products">
          {productsQuery.isLoading ? (
            <LoadingSkeleton rows={6} />
          ) : productsQuery.isError ? (
            <ErrorState title="Unable to load products" message="Product data could not be loaded." retry={() => productsQuery.refetch()} />
          ) : products.length ? (
            <div className="space-y-4">
              <div className="rounded-[1.35rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(248,250,252,0.98),rgba(239,246,255,0.82))] px-5 py-4">
                <p className="text-sm font-semibold text-slate-950">Operator-first product workspace</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Review synced catalog data, spot inventory edge cases, and jump into the draft workflow for products that need human-polished content.
                </p>
              </div>

              <div className="space-y-3">
                {products.map((product) => (
                  <Link
                    key={product.id}
                    to={`/app/catalog/${storeId}/products/${product.id}`}
                    className="block rounded-[1.35rem] border border-slate-200 bg-white px-5 py-4 transition hover:-translate-y-[1px] hover:border-accent-300 hover:bg-slate-50"
                  >
                    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_0.82fr_auto]">
                      <div className="min-w-0 space-y-3">
                        <div className="flex items-start gap-3">
                          <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-accent-700">
                            <Package2 className="h-4 w-4" />
                          </span>
                          <div className="min-w-0 space-y-1">
                            <p className="truncate font-semibold text-slate-950">{product.title}</p>
                            <p className="truncate text-sm text-slate-600">{product.handle}</p>
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <ProductStatusBadge status={product.status} />
                          <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-600">
                            Inventory {product.inventory_total}
                          </span>
                        </div>
                      </div>

                      <div className="grid gap-3 text-sm text-slate-600 sm:grid-cols-2 xl:grid-cols-1">
                        <div>
                          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Updated</p>
                          <p className="mt-2">{formatDate(product.updated_at)}</p>
                        </div>
                        <div>
                          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Catalog state</p>
                          <p className="mt-2 leading-6">
                            {formatCatalogState(product)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between gap-3 xl:justify-end">
                        <div className="text-sm font-medium text-accent-600">Open workspace</div>
                        <ArrowUpRight className="h-4 w-4 text-slate-400" />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState title="No products yet" message="Run a sync to load the store catalog." />
          )}
        </SectionCard>

        <div className="space-y-6 xl:sticky xl:top-24 xl:self-start">
          <div className="surface-panel p-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Catalog pulse</p>
            <div className="mt-5 space-y-3">
              <div className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Synced products</p>
                <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{products.length}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">Products currently available in the selected store workspace.</p>
              </div>
              <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
                <div className="rounded-[1.15rem] border border-emerald-200 bg-emerald-50 px-4 py-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-700">Active</p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{activeProducts}</p>
                </div>
                <div className="rounded-[1.15rem] border border-amber-200 bg-amber-50 px-4 py-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-700">Draft</p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{draftProducts}</p>
                </div>
                <div className="rounded-[1.15rem] border border-rose-200 bg-rose-50 px-4 py-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-rose-700">Zero inventory</p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{zeroInventoryProducts}</p>
                </div>
              </div>
            </div>
          </div>

          <SectionCard title="Workflow guidance">
            <div className="space-y-3 text-sm leading-6 text-slate-600">
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                Open a product workspace when content, SEO, or tags need human-reviewed AI draft updates.
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                Keep product edits in draft state until the approval flow confirms they are ready to publish.
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                Use inventory and status context together so copy changes do not ignore operational reality.
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}

export function ProductDetailPage() {
  const { storeId = "", productId = "" } = useParams();
  const productQuery = useProduct(storeId, productId);
  const draftsQuery = useProductDrafts(storeId, productId);
  const [draftForm, setDraftForm] = React.useState({
    generated_title: "",
    generated_description: "",
    generated_seo_title: "",
    generated_seo_description: "",
    generated_tags: ""
  });
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

  const refreshDraftData = () => {
    draftsQuery.refetch();
    productQuery.refetch();
  };
  const generateMutation = useGenerateProductDraft(storeId, productId, refreshDraftData);
  const updateMutation = useUpdateProductDraft(storeId, productId, activeDraft?.id ?? null, refreshDraftData);
  const submitApprovalMutation = useSubmitProductDraftForApproval(storeId, productId, activeDraft?.id ?? null, refreshDraftData);

  if (productQuery.isLoading) return <LoadingSkeleton rows={6} />;
  if (productQuery.isError) return <ErrorState title="Unable to load product" message="The selected product could not be loaded." retry={() => productQuery.refetch()} />;

  const product = productQuery.data!;

  return (
    <div className="space-y-8">
      <PageHeader
        title={product.title}
        description="Review live product context, generate draft content, and submit the draft for approval."
        actions={
          <Link to={`/app/catalog/${storeId}/products`}>
            <Button variant="secondary">Back to catalog</Button>
          </Link>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(23rem,0.95fr)]">
        <div className="space-y-6">
          <div className="surface-panel overflow-hidden border-accent-200 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.24),transparent_42%),linear-gradient(135deg,#eff6ff,#ffffff_58%,#f8fafc)] p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="max-w-2xl">
                <div className="inline-flex items-center gap-2 rounded-full border border-white/90 bg-white/90 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-accent-700">
                  <Boxes className="h-3.5 w-3.5" />
                  Product workspace
                </div>
                <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Live merchandising context</p>
                <p className="mt-2 text-sm leading-7 text-slate-600">
                  Use this workspace to inspect live merchandising context, refine AI-generated copy, and route changes into approval without losing operational detail.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <ProductStatusBadge status={product.status} />
                <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-600">
                  Vendor {formatVendorName(product.vendor)}
                </span>
              </div>
            </div>

            <div className="mt-6 grid gap-3 md:grid-cols-4">
              <div className="rounded-[1.2rem] border border-white/80 bg-white/88 px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Inventory</p>
                <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{product.inventory_total}</p>
              </div>
              <div className="rounded-[1.2rem] border border-white/80 bg-white/88 px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Variants</p>
                <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{product.variants.length}</p>
              </div>
              <div className="rounded-[1.2rem] border border-white/80 bg-white/88 px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Handle</p>
                <p className="mt-2 truncate text-sm font-medium text-slate-800">{product.handle}</p>
              </div>
              <div className="rounded-[1.2rem] border border-white/80 bg-white/88 px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Updated</p>
                <p className="mt-2 text-sm font-medium text-slate-800">{formatDate(product.updated_at)}</p>
              </div>
            </div>
          </div>

          <SectionCard title="Live product context">
            <KeyValueGrid
              items={[
                { label: "Handle", value: product.handle },
                { label: "SEO Title", value: product.seo_title ?? "-" },
                { label: "Updated", value: formatDate(product.updated_at) },
                { label: "Primary Variant", value: product.variants[0]?.title ?? "-" }
              ]}
            />
          </SectionCard>

          <SectionCard title="Variants">
            <div className="space-y-3">
              {product.variants.map((variant) => (
                <div key={variant.id} className="rounded-[1.25rem] border border-slate-200 bg-slate-50/80 px-4 py-4">
                  <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_0.7fr_0.6fr_0.6fr]">
                    <div>
                      <p className="font-medium text-slate-950">{variant.title}</p>
                      <p className="mt-1 text-sm text-slate-600">{variant.sku ?? "No SKU assigned"}</p>
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Price</p>
                      <p className="mt-2 text-sm text-slate-800">{variant.price}</p>
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Inventory</p>
                      <p className="mt-2 text-sm text-slate-800">{variant.inventory_quantity}</p>
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Channel record</p>
                      <p className="mt-2 text-sm text-slate-800">{formatVariantRecordLabel(variant.external_variant_id)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

        <div className="space-y-6 xl:sticky xl:top-24 xl:self-start">
          <SectionCard
            title="AI draft workshop"
            actions={
              <div className="flex flex-wrap gap-3">
                <Button variant="secondary" onClick={() => generateMutation.mutate()}>
                  {generateMutation.isPending ? "Generating..." : "Regenerate"}
                </Button>
                {activeDraft ? (
                  <Button
                    onClick={() =>
                      updateMutation.mutate({
                        generated_title: draftForm.generated_title || null,
                        generated_description: draftForm.generated_description || null,
                        generated_seo_title: draftForm.generated_seo_title || null,
                        generated_seo_description: draftForm.generated_seo_description || null,
                        generated_tags: draftForm.generated_tags.split(",").map((item) => item.trim()).filter(Boolean)
                      })
                    }
                    disabled={updateMutation.isPending}
                  >
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
                <Textarea
                  placeholder="Generated description"
                  value={normalizeGeneratedDescription(draftForm.generated_description)}
                  onChange={(event) => setDraftForm((current) => ({ ...current, generated_description: event.target.value }))}
                />
                <Input placeholder="Generated SEO title" value={draftForm.generated_seo_title} onChange={(event) => setDraftForm((current) => ({ ...current, generated_seo_title: event.target.value }))} />
                <Textarea placeholder="Generated SEO description" value={draftForm.generated_seo_description} onChange={(event) => setDraftForm((current) => ({ ...current, generated_seo_description: event.target.value }))} />
                <Input placeholder="tag-one, tag-two" value={draftForm.generated_tags} onChange={(event) => setDraftForm((current) => ({ ...current, generated_tags: event.target.value }))} />
                <Card className="border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-center gap-2">
                    <Tag className="h-4 w-4 text-slate-400" />
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Approval submission reason</p>
                  </div>
                  <Textarea className="mt-3" value={approvalReason} onChange={(event) => setApprovalReason(event.target.value)} />
                </Card>
                <Button className="w-full" onClick={() => submitApprovalMutation.mutate(approvalReason)} disabled={submitApprovalMutation.isPending}>
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

          <div className="surface-panel p-5">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-accent-600" />
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Operator guidance</p>
            </div>
            <div className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                Keep generated copy grounded to the live product, inventory state, and merchandising context.
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                Save draft changes before submitting so reviewers see the exact final text you intend to approve.
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                Route publication through approvals so content updates remain auditable and human-controlled.
              </div>
            </div>
          </div>

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
