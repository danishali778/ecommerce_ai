import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { inventoryApi } from "@frontend/api-client";
import { Button, Input } from "@frontend/ui";
import {
  DetailPanel,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
  PageHeader,
  SectionCard,
  StatusPill,
  SupplierDraftCard
} from "@/components/common";
import { formatDate, formatJson } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

export function InventoryPage() {
  const { storeId = "" } = useParams();
  const queryClient = useQueryClient();
  const [selectedSuggestionId, setSelectedSuggestionId] = useState("");

  const alertsQuery = useQuery({
    queryKey: ["inventory", "alerts", storeId],
    queryFn: () => inventoryApi.listAlerts(storeId),
    enabled: Boolean(storeId)
  });

  const suggestionsQuery = useQuery({
    queryKey: ["inventory", "suggestions", storeId],
    queryFn: () => inventoryApi.listSuggestions(storeId),
    enabled: Boolean(storeId)
  });

  useEffect(() => {
    if (!selectedSuggestionId && suggestionsQuery.data?.[0]?.id) {
      setSelectedSuggestionId(suggestionsQuery.data[0].id);
    }
  }, [selectedSuggestionId, suggestionsQuery.data]);

  const selectedSuggestion = useMemo(
    () => (suggestionsQuery.data ?? []).find((suggestion) => suggestion.id === selectedSuggestionId) ?? null,
    [selectedSuggestionId, suggestionsQuery.data]
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
    } else if (selectedSuggestion) {
      setDraftForm({
        vendor_name: String(selectedSuggestion.rationale_json.vendor_name ?? "Supplier"),
        recipient_email: "",
        subject: `Reorder request - ${selectedSuggestion.id}`,
        body: `Please prepare a reorder for ${selectedSuggestion.recommended_quantity} units.`,
        status: "draft"
      });
    }
  }, [selectedSuggestion]);

  const saveDraft = useMutation({
    mutationFn: () =>
      selectedSuggestion
        ? inventoryApi.createOrRefreshSupplierDraft(storeId, selectedSuggestion.id, draftForm)
        : Promise.reject(new Error("No suggestion selected")),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory", "suggestions", storeId] });
    }
  });

  const alerts = alertsQuery.data ?? [];
  const suggestions = suggestionsQuery.data ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Inventory alerts and reorder"
        description="Review low-stock signals, inspect suggestion rationale, and maintain supplier drafts without triggering direct external actions."
      />

      <div className="grid gap-4 md:grid-cols-3">
        <DetailPanel title="Out of stock" subtitle="Variants that need immediate attention">
          <p className="text-3xl font-semibold text-slate-950">{alerts.filter((item) => item.current_quantity <= 0).length}</p>
        </DetailPanel>
        <DetailPanel title="Low stock" subtitle="Variants below threshold">
          <p className="text-3xl font-semibold text-slate-950">{alerts.length}</p>
        </DetailPanel>
        <DetailPanel title="Awaiting reorder" subtitle="Suggestions currently open">
          <p className="text-3xl font-semibold text-slate-950">{suggestions.length}</p>
        </DetailPanel>
      </div>

      {suggestionsQuery.isLoading ? (
        <LoadingSkeleton rows={6} />
      ) : suggestionsQuery.isError ? (
        <ErrorState title="Could not load inventory suggestions" message={messageFromError(suggestionsQuery.error)} />
      ) : suggestions.length === 0 ? (
        <EmptyState title="No reorder suggestions" message="Sync more product inventory to generate low-stock alerts and reorder guidance." />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <SectionCard title="Suggestions and alerts">
            <div className="space-y-3">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion.id}
                  className={`w-full rounded-2xl border p-4 text-left ${
                    suggestion.id === selectedSuggestionId ? "border-accent-300 bg-accent-50" : "border-slate-200 bg-white"
                  }`}
                  onClick={() => setSelectedSuggestionId(suggestion.id)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-950">{suggestion.product_id}</p>
                      <p className="mt-1 text-sm text-slate-600">
                        Recommended quantity {suggestion.recommended_quantity} · Current quantity {suggestion.current_quantity}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">Created {formatDate(suggestion.created_at)}</p>
                    </div>
                    <StatusPill value={suggestion.status} />
                  </div>
                </button>
              ))}
            </div>
          </SectionCard>

          {selectedSuggestion ? (
            <div className="space-y-6">
              <DetailPanel title="Reorder details" subtitle="Inspect the AI suggestion and maintain the supplier communication draft.">
                <KeyValueGrid
                  items={[
                    { label: "Suggestion", value: selectedSuggestion.id },
                    { label: "Recommended quantity", value: selectedSuggestion.recommended_quantity },
                    { label: "Current quantity", value: selectedSuggestion.current_quantity },
                    { label: "Threshold", value: selectedSuggestion.threshold_value }
                  ]}
                />
              </DetailPanel>

              <SectionCard title="AI suggestion rationale">
                <pre className="whitespace-pre-wrap text-sm leading-7 text-slate-700">{formatJson(selectedSuggestion.rationale_json)}</pre>
              </SectionCard>

              <SectionCard title="Supplier communication draft">
                <div className="space-y-4">
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
                  <Input
                    value={draftForm.subject}
                    onChange={(event) => setDraftForm((current) => ({ ...current, subject: event.target.value }))}
                    placeholder="Draft subject"
                  />
                  <textarea
                    className="min-h-48 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm shadow-soft outline-none transition focus:border-accent-300 focus:ring-4 focus:ring-accent-100"
                    value={draftForm.body}
                    onChange={(event) => setDraftForm((current) => ({ ...current, body: event.target.value }))}
                  />

                  <div className="flex flex-wrap gap-3">
                    <Button onClick={() => saveDraft.mutate()} disabled={saveDraft.isPending}>
                      {saveDraft.isPending ? "Saving..." : "Save supplier draft"}
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => navigator.clipboard.writeText(draftForm.body)}
                    >
                      Copy draft
                    </Button>
                  </div>
                  <p className="text-sm text-slate-500">
                    Supplier outreach remains draft-only in CommerceOps. Save and review here, then send externally from your purchasing workflow.
                  </p>
                  {selectedSuggestion.supplier_draft ? (
                    <SupplierDraftCard subject={selectedSuggestion.supplier_draft.subject} body={selectedSuggestion.supplier_draft.body} />
                  ) : null}
                </div>
              </SectionCard>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
