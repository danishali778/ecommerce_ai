import { fireEvent, screen, waitFor } from "@testing-library/react";

import { FraudDetailPage } from "@/pages";
import { renderWithProviders } from "@/test/utils";

const getRiskReviewMock = vi.fn();
const getOrderMock = vi.fn();
const recordDecisionMock = vi.fn();

vi.mock("@frontend/api-client", async () => {
  const actual = await vi.importActual<object>("@frontend/api-client");
  const base = actual as Record<string, any>;
  return {
    ...base,
    fraudApi: {
      ...base.fraudApi,
      getRiskReview: (...args: unknown[]) => getRiskReviewMock(...args),
      recordDecision: (...args: unknown[]) => recordDecisionMock(...args)
    },
    catalogApi: {
      ...base.catalogApi,
      getOrder: (...args: unknown[]) => getOrderMock(...args)
    }
  };
});

describe("fraud detail page", () => {
  beforeEach(() => {
    getRiskReviewMock.mockResolvedValue({
      id: "review-1",
      order_id: "order-1",
      risk_score: 94,
      risk_status: "critical_risk",
      reason_codes_json: ["ip_shipping_mismatch", "suspicious_email_domain"],
      decision: null,
      decision_notes: null,
      reviewed_by_user_id: null,
      reviewed_at: null,
      created_at: "2026-05-26T10:00:00.000Z",
      updated_at: "2026-05-26T10:10:00.000Z"
    });
    getOrderMock.mockResolvedValue({
      id: "order-1",
      external_order_id: "ORD-8942-X",
      status: "open",
      payment_status: "paid",
      fulfillment_status: "unfulfilled",
      total: "1450.00",
      currency: "USD",
      created_at: "2026-05-26T10:00:00.000Z"
    });
    recordDecisionMock.mockResolvedValue({});
  });

  it("keeps fraud decisions internal and non-mutating in the UI", async () => {
    renderWithProviders(<FraudDetailPage />, {
      route: "/app/fraud/store-1/reviews/review-1",
      path: "/app/fraud/:storeId/reviews/:riskReviewId"
    });

    expect(await screen.findByText("Record decision")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve Order" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hold for Review" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject / Escalate" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cancel & Refund" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Hold for Review" }));

    await waitFor(() => {
      expect(recordDecisionMock).toHaveBeenCalledWith("store-1", "review-1", "held", "");
    });
  });
});
