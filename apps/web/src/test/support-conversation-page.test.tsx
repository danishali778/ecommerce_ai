import { screen } from "@testing-library/react";

import { SupportConversationPage } from "@/pages";
import { renderWithProviders } from "@/test/utils";

const getConversationMock = vi.fn();
const listMessagesMock = vi.fn();
const getCustomerMock = vi.fn();
const getOrderMock = vi.fn();

vi.mock("@frontend/api-client", async () => {
  const actual = await vi.importActual<object>("@frontend/api-client");
  return {
    ...actual,
    supportApi: {
      ...(actual as Record<string, unknown>).supportApi,
      getConversation: (...args: unknown[]) => getConversationMock(...args),
      listMessages: (...args: unknown[]) => listMessagesMock(...args),
      updateConversation: vi.fn(),
      createMessage: vi.fn(),
      generateDraft: vi.fn()
    },
    catalogApi: {
      ...(actual as Record<string, unknown>).catalogApi,
      getCustomer: (...args: unknown[]) => getCustomerMock(...args),
      getOrder: (...args: unknown[]) => getOrderMock(...args)
    }
  };
});

describe("support conversation page", () => {
  beforeEach(() => {
    getConversationMock.mockResolvedValue({
      id: "conv-1",
      store_id: "store-1",
      customer_id: "customer-1",
      order_id: "order-1",
      external_ticket_id: "ticket-1",
      channel: "internal_console",
      status: "pending_review",
      assigned_user_id: null,
      created_at: "2026-05-26T10:00:00.000Z",
      updated_at: "2026-05-26T10:10:00.000Z"
    });
    listMessagesMock.mockResolvedValue([
      {
        id: "msg-1",
        conversation_id: "conv-1",
        direction: "draft_outbound",
        body: "Draft support reply",
        generated_by_ai: true,
        confidence_score: 0.7,
        needs_human_review: true,
        review_reason_code: "low_confidence",
        status: "pending_review",
        cited_policy_chunks_json: [{ chunk_id: "chunk-1", rationale: "Returns policy" }],
        cited_order_facts_summary: "Paid order",
        created_at: "2026-05-26T10:00:00.000Z",
        updated_at: "2026-05-26T10:10:00.000Z"
      }
    ]);
    getCustomerMock.mockResolvedValue({
      id: "customer-1",
      email: "customer@example.com",
      first_name: "Sarah",
      last_name: "Jenkins",
      total_orders: 2,
      created_at: "2026-05-25T10:00:00.000Z"
    });
    getOrderMock.mockResolvedValue({
      id: "order-1",
      external_order_id: "ORD-1",
      status: "open",
      payment_status: "paid",
      fulfillment_status: "unfulfilled",
      total: "120.00",
      currency: "USD",
      created_at: "2026-05-25T10:00:00.000Z"
    });
  });

  it("keeps support output in manual-send semantics", async () => {
    renderWithProviders(<SupportConversationPage />, {
      route: "/app/support/store-1/conversations/conv-1",
      path: "/app/support/:storeId/conversations/:conversationId"
    });

    expect(await screen.findByText("Operator next steps")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark ready for manual send" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve & Send" })).not.toBeInTheDocument();
  });
});
