import { fireEvent, screen, waitFor } from "@testing-library/react";

import { InventoryPage } from "@/pages";
import { renderWithProviders } from "@/test/utils";

const listAlertsMock = vi.fn();
const listSuggestionsMock = vi.fn();
const createSupplierDraftMock = vi.fn();

vi.mock("@frontend/api-client", async () => {
  const actual = await vi.importActual<object>("@frontend/api-client");
  const base = actual as Record<string, any>;
  return {
    ...base,
    inventoryApi: {
      ...base.inventoryApi,
      listAlerts: (...args: unknown[]) => listAlertsMock(...args),
      listSuggestions: (...args: unknown[]) => listSuggestionsMock(...args),
      createOrRefreshSupplierDraft: (...args: unknown[]) => createSupplierDraftMock(...args)
    }
  };
});

describe("inventory page", () => {
  beforeEach(() => {
    listAlertsMock.mockResolvedValue([
      {
        id: "alert-1",
        product_id: "product-1",
        variant_id: "variant-1",
        threshold_value: 12,
        current_quantity: 3,
        status: "open",
        created_at: "2026-05-26T10:00:00.000Z",
        updated_at: "2026-05-26T10:10:00.000Z"
      }
    ]);
    listSuggestionsMock.mockResolvedValue([
      {
        id: "suggestion-1",
        inventory_alert_id: "alert-1",
        product_id: "product-1",
        variant_id: "SKU-123",
        recommended_quantity: 250,
        current_quantity: 3,
        threshold_value: 12,
        rationale_json: {
          vendor_name: "Apex Furnishings",
          lead_time_days: 14,
          estimated_cost: 12500,
          summary: "Reorder before stockout."
        },
        status: "open",
        created_at: "2026-05-26T10:00:00.000Z",
        updated_at: "2026-05-26T10:10:00.000Z",
        supplier_draft: null
      }
    ]);
    createSupplierDraftMock.mockResolvedValue({});
  });

  it("keeps supplier communication draft-oriented", async () => {
    renderWithProviders(<InventoryPage />, { route: "/app/inventory/store-1", path: "/app/inventory/:storeId" });

    expect(await screen.findByText("Supplier communication draft")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save Supplier Draft" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark Ready for Review" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Submit Reorder for Approval" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Mark Ready for Review" }));

    await waitFor(() => {
      expect(createSupplierDraftMock).toHaveBeenCalledWith(
        "store-1",
        "suggestion-1",
        expect.objectContaining({ status: "ready_for_review" })
      );
    });
  });
});
