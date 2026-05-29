import { fireEvent, screen, waitFor } from "@testing-library/react";

import { ProductDetailPage } from "@/pages";
import { renderWithProviders } from "@/test/utils";

const getProductMock = vi.fn();
const listDraftsMock = vi.fn();
const updateDraftMock = vi.fn();
const submitDraftForApprovalMock = vi.fn();

vi.mock("@frontend/api-client", async () => {
  const actual = await vi.importActual<object>("@frontend/api-client");
  const base = actual as Record<string, any>;
  return {
    ...base,
    catalogApi: {
      ...base.catalogApi,
      getProduct: (...args: unknown[]) => getProductMock(...args),
      listDrafts: (...args: unknown[]) => listDraftsMock(...args),
      updateDraft: (...args: unknown[]) => updateDraftMock(...args),
      submitDraftForApproval: (...args: unknown[]) => submitDraftForApprovalMock(...args),
      generateDraft: vi.fn()
    }
  };
});

describe("product detail page", () => {
  beforeEach(() => {
    getProductMock.mockResolvedValue({
      id: "product-1",
      title: "Ergonomic Chair",
      handle: "ergonomic-chair",
      vendor: "CommerceOps",
      status: "active",
      seo_title: "Ergonomic Chair",
      inventory_total: 42,
      updated_at: "2026-05-26T10:00:00.000Z",
      variants: [{ id: "var-1", external_variant_id: "1", title: "Default", sku: "CHAIR-1", price: "199.00", inventory_quantity: 42 }],
      latest_draft: null
    });
    listDraftsMock.mockResolvedValue([
      {
        id: "draft-1",
        product_id: "product-1",
        generated_title: "Ergonomic Chair",
        generated_description: "Draft description",
        generated_tags: ["ergonomic"],
        generated_seo_title: "SEO title",
        generated_seo_description: "SEO description",
        model_name: "gpt-4o",
        status: "pending_review",
        created_at: "2026-05-26T10:00:00.000Z",
        updated_at: "2026-05-26T10:10:00.000Z"
      }
    ]);
    updateDraftMock.mockResolvedValue({});
    submitDraftForApprovalMock.mockResolvedValue({
      approval_id: "approval-1",
      approval_status: "pending",
      draft_status: "pending_review"
    });
  });

  it("submits the draft for approval from operator mode", async () => {
    renderWithProviders(<ProductDetailPage />, {
      route: "/app/catalog/store-1/products/product-1",
      path: "/app/catalog/:storeId/products/:productId"
    });

    expect(await screen.findByRole("heading", { name: "Ergonomic Chair" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Submit for Approval" }));

    await waitFor(() => {
      expect(submitDraftForApprovalMock).toHaveBeenCalledWith("store-1", "product-1", "draft-1", "Draft is ready for review.");
    });
  });
});
