import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";

import { AppShell } from "@/components/shell";
import { createTestQueryClient } from "@/test/utils";

const useAuthMock = vi.fn();
const useAppStateMock = vi.fn();
const notificationsListMock = vi.fn();

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => useAuthMock()
}));

vi.mock("@/hooks/use-app-state", () => ({
  useAppState: () => useAppStateMock()
}));

vi.mock("@frontend/api-client", async () => {
  const actual = await vi.importActual<object>("@frontend/api-client");
  return {
    ...actual,
    notificationsApi: {
      list: (...args: unknown[]) => notificationsListMock(...args),
      markRead: vi.fn()
    }
  };
});

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
}

describe("store switcher", () => {
  it("updates selected store and redirects store-scoped routes", async () => {
    const setSelectedStoreId = vi.fn();
    const client = createTestQueryClient();
    notificationsListMock.mockResolvedValue([]);
    useAuthMock.mockReturnValue({
      me: {
        user: { id: "u1", full_name: "Operator One", email: "operator@example.com", status: "active" },
        organization: { id: "org-1", name: "CommerceOps", slug: "commerceops", status: "active" },
        roles: ["operator"],
        permissions: ["catalog.read", "notifications.read"],
        accessible_stores: [
          { id: "store-a", name: "Store A", domain: "a.myshopify.com", platform: "shopify", connection_status: "connected", created_at: "", updated_at: "" },
          { id: "store-b", name: "Store B", domain: "b.myshopify.com", platform: "shopify", connection_status: "connected", created_at: "", updated_at: "" }
        ]
      },
      logout: vi.fn(),
      initialized: true,
      isAuthenticated: true
    });
    useAppStateMock.mockReturnValue({
      selectedStoreId: "store-a",
      setSelectedStoreId,
      sidebarOpen: true,
      setSidebarOpen: vi.fn()
    });

    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/app/catalog/store-a/products"]}>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/app/catalog/:storeId/products" element={<LocationProbe />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    fireEvent.change(screen.getByDisplayValue("Store A"), { target: { value: "store-b" } });

    expect(setSelectedStoreId).toHaveBeenCalledWith("store-b");
    expect(await screen.findByTestId("location")).toHaveTextContent("/app/catalog/store-b/products");
  });
});
