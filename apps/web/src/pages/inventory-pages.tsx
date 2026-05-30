import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Clipboard, FilePenLine, PackageSearch, Search, Truck } from "lucide-react";

import { Button, Card, Input, Select, Textarea } from "@frontend/ui";
import {
  DetailPanel,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
  MetricCard,
  PageHeader,
  SectionCard,
  StatusPill,
  SupplierDraftCard
} from "@/components/common";
import { useProducts } from "@/hooks/use-catalog";
import { useInventoryAlerts, useReorderSuggestions, useSaveSupplierDraft } from "@/hooks/use-inventory";
import { formatDate } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function numberFromRationale(value: unknown, fallback = 0) {
  return typeof value === "number" ? value : fallback;
}

function stringFromRationale(value: unknown, fallback = "Unknown") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function uuidLike(value?: string | null) {
  if (!value) return false;
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value.trim());
}

function readableInventoryValue(value?: string | null) {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed || uuidLike(trimmed)) return null;
  return trimmed;
}

function inventoryDisplayName({
  productId,
  variantId,
  productTitle,
  rationale
}: {
  productId: string;
  variantId?: string | null;
  productTitle?: string | null;
  rationale?: Record<string, unknown>;
}) {
  const readableProductTitle = readableInventoryValue(productTitle);
  if (readableProductTitle) return readableProductTitle;

  const rationaleCandidates = rationale
    ? [
        rationale.product_title,
        rationale.variant_title,
        rationale.product_name,
        rationale.variant_name,
        rationale.sku
      ]
    : [];

  for (const candidate of rationaleCandidates) {
    if (typeof candidate === "string") {
      const readable = readableInventoryValue(candidate);
      if (readable) return readable;
    }
  }

  return readableInventoryValue(variantId) ?? readableInventoryValue(productId) ?? "Inventory item";
}

function inventoryDisplayMeta({
  productId,
  variantId,
  productTitle,
  rationale
}: {
  productId: string;
  variantId?: string | null;
  productTitle?: string | null;
  rationale?: Record<string, unknown>;
}): string | null {
  const sku = rationale && typeof rationale.sku === "string" ? readableInventoryValue(rationale.sku) : null;
  const readableVariant = readableInventoryValue(variantId);
  const readableProduct = readableInventoryValue(productId);
  const readableProductTitle = readableInventoryValue(productTitle);
  const readableVariantTitle =
    rationale && typeof rationale.variant_title === "string" ? readableInventoryValue(rationale.variant_title) : null;

  if (sku) return `SKU ${sku}`;
  if (readableVariantTitle && readableVariantTitle !== readableProductTitle) return readableVariantTitle;
  if (readableVariant && readableProduct && readableVariant !== readableProduct) return readableVariant;
  if (readableProduct && readableProduct !== readableProductTitle) return readableProduct;
  return null;
}

export function InventoryPage() {
  const { storeId = "" } = useParams();
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selectedSuggestionId, setSelectedSuggestionId] = useState("");
  const [ignoredIds, setIgnoredIds] = useState<string[]>([]);

  const alertsQuery = useInventoryAlerts(storeId, statusFilter || undefined);
  const suggestionsQuery = useReorderSuggestions(storeId, statusFilter || undefined);
  const productsQuery = useProducts(storeId);
  const productsById = useMemo(() => new Map((productsQuery.data ?? []).map((product) => [product.id, product])), [productsQuery.data]);

  const suggestions = useMemo(
    () =>
      (suggestionsQuery.data ?? []).filter((suggestion) => {
        if (ignoredIds.includes(suggestion.id)) return false;
        if (!search) return true;
        return [suggestion.id, suggestion.product_id, suggestion.variant_id ?? "", suggestion.status]
          .join(" ")
          .toLowerCase()
          .includes(search.toLowerCase());
      }),
    [ignoredIds, search, suggestionsQuery.data]
  );

  useEffect(() => {
    if (!selectedSuggestionId && suggestions[0]?.id) {
      setSelectedSuggestionId(suggestions[0].id);
    }
    if (selectedSuggestionId && !suggestions.find((suggestion) => suggestion.id === selectedSuggestionId)) {
      setSelectedSuggestionId(suggestions[0]?.id ?? "");
    }
  }, [selectedSuggestionId, suggestions]);

  const selectedSuggestion = useMemo(() => {
    if (!suggestions.length) return null;
    if (!selectedSuggestionId) return suggestions[0] ?? null;
    return suggestions.find((suggestion) => suggestion.id === selectedSuggestionId) ?? suggestions[0] ?? null;
  }, [selectedSuggestionId, suggestions]);

  const [draftForm, setDraftForm] = useState({
    vendor_name: "",
    recipient_email: "",
    subject: "",
    body: "",
    status: "draft"
  });

  useEffect(() => {
    if (selectedSuggestion?.supplier_draft) {
      setDraftForm({
        vendor_name: selectedSuggestion.supplier_draft.vendor_name,
        recipient_email: selectedSuggestion.supplier_draft.recipient_email ?? "",
        subject: selectedSuggestion.supplier_draft.subject,
        body: selectedSuggestion.supplier_draft.body,
        status: selectedSuggestion.supplier_draft.status
      });
      return;
    }

    if (selectedSuggestion) {
      const vendor = stringFromRationale(selectedSuggestion.rationale_json.vendor_name, "Supplier");
      const productTitle = productsById.get(selectedSuggestion.product_id)?.title;
      const suggestionItemLabel = inventoryDisplayName({
        productId: selectedSuggestion.product_id,
        variantId: selectedSuggestion.variant_id,
        productTitle,
        rationale: selectedSuggestion.rationale_json
      });
      setDraftForm({
        vendor_name: vendor,
        recipient_email: "",
        subject: `Reorder request - ${suggestionItemLabel}`,
        body: `Hello ${vendor} team,\n\nPlease prepare a reorder for ${selectedSuggestion.recommended_quantity} units. We are reviewing the current stock velocity and will handle final send manually after approval.\n`,
        status: "draft"
      });
    }
  }, [productsById, selectedSuggestion]);

  const saveDraft = useSaveSupplierDraft(storeId, selectedSuggestion?.id ?? null);

  const alerts = alertsQuery.data ?? [];
  const outOfStock = alerts.filter((item) => item.current_quantity <= 0).length;
  const lowStock = alerts.filter((item) => item.current_quantity > 0).length;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Inventory alerts and reorder"
        description="Review low-stock signals, inspect recommendation rationale, and keep supplier communication as draft-only internal work."
        actions={
          <div className="flex flex-wrap gap-3">
            <div className="relative min-w-56">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search SKU or product" />
            </div>
            <Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="w-44">
              <option value="">All statuses</option>
              <option value="open">Open</option>
              <option value="pending_review">Pending review</option>
              <option value="resolved">Resolved</option>
            </Select>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Out of Stock" value={outOfStock} hint="Inventory alerts at zero quantity" tone={outOfStock ? "danger" : "success"} />
        <MetricCard label="Low Stock" value={lowStock} hint="Variants below threshold but still available" tone={lowStock ? "warning" : "success"} />
        <MetricCard label="Awaiting Reorder" value={suggestions.length} hint="Suggestions still being reviewed" tone={suggestions.length ? "info" : "success"} />
      </div>

      {suggestionsQuery.isLoading ? (
        <LoadingSkeleton rows={6} />
      ) : suggestionsQuery.isError ? (
        <ErrorState title="Could not load inventory suggestions" message={messageFromError(suggestionsQuery.error)} />
      ) : suggestions.length === 0 ? (
        <EmptyState
          title="No reorder suggestions"
          message="Sync more product inventory to generate low-stock alerts and reorder guidance."
        />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(22rem,26rem)]">
          <div className="space-y-6">
            <SectionCard title="Critical inventory alerts">
              {alertsQuery.isLoading ? (
                <LoadingSkeleton rows={4} />
              ) : alertsQuery.isError ? (
                <ErrorState title="Could not load alerts" message={messageFromError(alertsQuery.error)} />
              ) : alerts.length === 0 ? (
                <EmptyState title="No inventory alerts" message="Inventory alerts will appear here once stock drops below configured thresholds." />
              ) : (
                <div className="space-y-3">
                  {alerts.map((alert) => {
                    const meta = inventoryDisplayMeta({
                      productId: alert.product_id,
                      variantId: alert.variant_id,
                      productTitle: productsById.get(alert.product_id)?.title
                    });

                    return (
                      <div key={alert.id} className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-4">
                        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                          <div className="min-w-0 space-y-2">
                            <div className="space-y-1">
                              <p className="font-medium text-slate-950">
                                {inventoryDisplayName({
                                  productId: alert.product_id,
                                  variantId: alert.variant_id,
                                  productTitle: productsById.get(alert.product_id)?.title
                                })}
                              </p>
                              {meta ? <p className="text-xs text-slate-500">{meta}</p> : null}
                            </div>
                            <div className="flex flex-wrap gap-2 text-xs font-medium text-slate-600">
                              <span className="rounded-full bg-white px-3 py-1">Threshold {alert.threshold_value}</span>
                              <span className="rounded-full bg-white px-3 py-1">Current {alert.current_quantity}</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-3 lg:justify-end">
                            <div className="text-right">
                              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Stock now</p>
                              <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">{alert.current_quantity}</p>
                            </div>
                            <StatusPill value={alert.status} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </SectionCard>

            <SectionCard title="Reorder suggestions">
              <div className="space-y-3">
                {suggestions.map((suggestion) => {
                  const meta = inventoryDisplayMeta({
                    productId: suggestion.product_id,
                    variantId: suggestion.variant_id,
                    productTitle: productsById.get(suggestion.product_id)?.title,
                    rationale: suggestion.rationale_json
                  });

                  return (
                    <button
                      key={suggestion.id}
                      className={`w-full rounded-2xl border p-4 text-left transition ${
                        suggestion.id === selectedSuggestionId ? "border-accent-300 bg-accent-50" : "border-slate-200 bg-white hover:border-accent-200 hover:bg-slate-50"
                      }`}
                      onClick={() => setSelectedSuggestionId(suggestion.id)}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex min-w-0 items-start gap-3">
                          <span className="mt-0.5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent-50 text-accent-700">
                            <PackageSearch className="h-4 w-4" />
                          </span>
                          <div className="min-w-0 space-y-2">
                            <div className="space-y-1">
                              <p className="font-semibold text-slate-950">
                                {inventoryDisplayName({
                                  productId: suggestion.product_id,
                                  variantId: suggestion.variant_id,
                                  productTitle: productsById.get(suggestion.product_id)?.title,
                                  rationale: suggestion.rationale_json
                                })}
                              </p>
                              {meta ? <p className="text-xs text-slate-500">{meta}</p> : null}
                            </div>
                            <div className="flex flex-wrap gap-2">
                              <StatusPill value={suggestion.status} />
                              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600">
                                Suggest {suggestion.recommended_quantity} units
                              </span>
                            </div>
                            <p className="text-sm text-slate-600">
                              Current stock {suggestion.current_quantity} / threshold {suggestion.threshold_value}
                            </p>
                          </div>
                        </div>
                        <p className="shrink-0 text-xs text-slate-500">{formatDate(suggestion.created_at)}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </SectionCard>
          </div>

          {selectedSuggestion ? (
            <div className="space-y-6 xl:sticky xl:top-24 xl:self-start">
              <DetailPanel title="Reorder details" subtitle="Inspect rationale, cost, and supplier draft state before any external follow-up.">
                <KeyValueGrid
                  items={[
                    { label: "Suggested quantity", value: selectedSuggestion.recommended_quantity },
                    { label: "Current stock", value: selectedSuggestion.current_quantity },
                    { label: "Threshold", value: selectedSuggestion.threshold_value },
                    {
                      label: "Lead time",
                      value: `${numberFromRationale(selectedSuggestion.rationale_json.lead_time_days, 14)} days`
                    }
                  ]}
                />
              </DetailPanel>

              <SectionCard title="AI suggestion rationale">
                <div className="space-y-4">
                  <Card className="border-slate-200 bg-slate-50 p-4">
                    <p className="font-medium text-slate-950">Recommendation summary</p>
                    <p className="mt-2 text-sm leading-7 text-slate-700">
                      {stringFromRationale(
                        selectedSuggestion.rationale_json.summary,
                        "Current stock velocity and supplier lead time suggest review is needed before stock falls below safe operational levels."
                      )}
                    </p>
                  </Card>
                  <KeyValueGrid
                    items={[
                      { label: "Supplier", value: stringFromRationale(selectedSuggestion.rationale_json.vendor_name, draftForm.vendor_name || "Supplier") },
                      { label: "Lead time", value: `${numberFromRationale(selectedSuggestion.rationale_json.lead_time_days, 14)} days` },
                      { label: "Estimated cost", value: `$${numberFromRationale(selectedSuggestion.rationale_json.estimated_cost, 0).toLocaleString()}` },
                      { label: "Created", value: formatDate(selectedSuggestion.created_at) }
                    ]}
                  />
                </div>
              </SectionCard>

              <SectionCard title="Supplier communication draft">
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <Input
                      value={draftForm.vendor_name}
                      onChange={(event) => setDraftForm((current) => ({ ...current, vendor_name: event.target.value }))}
                      placeholder="Vendor name"
                    />
                    <Input
                      value={draftForm.recipient_email}
                      onChange={(event) => setDraftForm((current) => ({ ...current, recipient_email: event.target.value }))}
                      placeholder="Recipient email"
                    />
                  </div>
                  <Input
                    value={draftForm.subject}
                    onChange={(event) => setDraftForm((current) => ({ ...current, subject: event.target.value }))}
                    placeholder="Draft subject"
                  />
                  <Textarea
                    rows={11}
                    value={draftForm.body}
                    onChange={(event) => setDraftForm((current) => ({ ...current, body: event.target.value }))}
                  />

                  <div className="flex flex-wrap gap-3">
                    <Button onClick={() => saveDraft.mutate({ ...draftForm, status: "draft" })} disabled={saveDraft.isPending || !selectedSuggestion}>
                      <FilePenLine className="mr-2 h-4 w-4" />
                      Save Supplier Draft
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => saveDraft.mutate({ ...draftForm, status: "ready_for_review" })}
                      disabled={saveDraft.isPending || !selectedSuggestion}
                    >
                      <Truck className="mr-2 h-4 w-4" />
                      Mark Ready for Review
                    </Button>
                    <Button variant="secondary" onClick={() => navigator.clipboard?.writeText(draftForm.body)}>
                      <Clipboard className="mr-2 h-4 w-4" />
                      Copy Draft
                    </Button>
                    <Button
                      variant="ghost"
                      className="text-slate-500 hover:text-slate-900"
                      onClick={() => {
                        setIgnoredIds((current) => [...current, selectedSuggestion.id]);
                        setSelectedSuggestionId("");
                      }}
                    >
                      Ignore Suggestion
                    </Button>
                  </div>

                  <p className="text-sm text-slate-500">
                    Reorder suggestions are recommendations only. Supplier outreach remains draft-only in CommerceOps and should be sent manually from your purchasing workflow.
                  </p>

                  {selectedSuggestion.supplier_draft ? (
                    <SupplierDraftCard subject={selectedSuggestion.supplier_draft.subject} body={selectedSuggestion.supplier_draft.body} />
                  ) : null}
                </div>
              </SectionCard>

              {saveDraft.isError ? (
                <ErrorState title="Could not save supplier draft" message={messageFromError(saveDraft.error)} />
              ) : null}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
