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

export function InventoryPage() {
  const { storeId = "" } = useParams();
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selectedSuggestionId, setSelectedSuggestionId] = useState("");
  const [ignoredIds, setIgnoredIds] = useState<string[]>([]);

  const alertsQuery = useInventoryAlerts(storeId, statusFilter || undefined);
  const suggestionsQuery = useReorderSuggestions(storeId, statusFilter || undefined);

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

  const selectedSuggestion = useMemo(
    () => suggestions.find((suggestion) => suggestion.id === selectedSuggestionId) ?? null,
    [selectedSuggestionId, suggestions]
  );

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
      setDraftForm({
        vendor_name: vendor,
        recipient_email: "",
        subject: `Reorder request - ${selectedSuggestion.variant_id ?? selectedSuggestion.product_id}`,
        body: `Hello ${vendor} team,\n\nPlease prepare a reorder for ${selectedSuggestion.recommended_quantity} units. We are reviewing the current stock velocity and will handle final send manually after approval.\n`,
        status: "draft"
      });
    }
  }, [selectedSuggestion]);

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
        <div className="grid gap-6 xl:grid-cols-[1.14fr_0.86fr]">
          <div className="space-y-6">
            <SectionCard title="Critical inventory alerts">
              {alertsQuery.isLoading ? (
                <LoadingSkeleton rows={4} />
              ) : alertsQuery.isError ? (
                <ErrorState title="Could not load alerts" message={messageFromError(alertsQuery.error)} />
              ) : alerts.length === 0 ? (
                <EmptyState title="No inventory alerts" message="Inventory alerts will appear here once stock drops below configured thresholds." />
              ) : (
                <div className="overflow-hidden rounded-2xl border border-slate-200">
                  <div className="grid grid-cols-[1.2fr_0.8fr_0.6fr_0.7fr] bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <div>Product / variant</div>
                    <div>Alert</div>
                    <div>Current</div>
                    <div>Status</div>
                  </div>
                  <div className="divide-y divide-slate-200">
                    {alerts.map((alert) => (
                      <div key={alert.id} className="grid grid-cols-[1.2fr_0.8fr_0.6fr_0.7fr] gap-3 px-4 py-4 text-sm text-slate-700">
                        <div className="space-y-1">
                          <p className="font-medium text-slate-950">{alert.product_id}</p>
                          <p className="text-xs text-slate-500">{alert.variant_id}</p>
                        </div>
                        <div>Threshold {alert.threshold_value}</div>
                        <div>{alert.current_quantity}</div>
                        <div><StatusPill value={alert.status} /></div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </SectionCard>

            <SectionCard title="Reorder suggestions">
              <div className="space-y-3">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion.id}
                    className={`w-full rounded-2xl border p-4 text-left transition ${
                      suggestion.id === selectedSuggestionId ? "border-accent-300 bg-accent-50" : "border-slate-200 bg-white hover:border-accent-200"
                    }`}
                    onClick={() => setSelectedSuggestionId(suggestion.id)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-accent-50 text-accent-700">
                            <PackageSearch className="h-4 w-4" />
                          </span>
                          <div>
                            <p className="font-semibold text-slate-950">{suggestion.variant_id ?? suggestion.product_id}</p>
                            <p className="text-xs text-slate-500">{suggestion.product_id}</p>
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <StatusPill value={suggestion.status} />
                          <StatusPill value={`reorder_${suggestion.recommended_quantity}`} />
                        </div>
                        <p className="text-sm text-slate-600">
                          Current {suggestion.current_quantity} - Threshold {suggestion.threshold_value}
                        </p>
                      </div>
                      <p className="text-xs text-slate-500">{formatDate(suggestion.created_at)}</p>
                    </div>
                  </button>
                ))}
              </div>
            </SectionCard>
          </div>

          {selectedSuggestion ? (
            <div className="space-y-6">
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
                  <Card className="border-blue-100 bg-blue-50 p-4">
                    <p className="font-medium text-blue-900">Recommendation summary</p>
                    <p className="mt-2 text-sm leading-7 text-blue-800">
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
                    <Button onClick={() => saveDraft.mutate({ ...draftForm, status: "draft" })} disabled={saveDraft.isPending}>
                      <FilePenLine className="mr-2 h-4 w-4" />
                      Save Supplier Draft
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => saveDraft.mutate({ ...draftForm, status: "ready_for_review" })}
                      disabled={saveDraft.isPending}
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
