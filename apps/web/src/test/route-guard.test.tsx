import { MemoryRouter } from "react-router-dom";
import { render, screen } from "@testing-library/react";

import { AppRoutes } from "@/routes";

const useAuthMock = vi.fn();
const useAppStateMock = vi.fn();

vi.mock("@/app/use-auth", () => ({
  useAuth: () => useAuthMock()
}));

vi.mock("@/app/use-app-state", () => ({
  useAppState: () => useAppStateMock()
}));

describe("protected routing", () => {
  beforeEach(() => {
    useAppStateMock.mockReturnValue({
      selectedStoreId: "store-1",
      setSelectedStoreId: vi.fn(),
      sidebarOpen: true,
      setSidebarOpen: vi.fn()
    });
  });

  it("redirects unauthenticated users to login from app routes", async () => {
    useAuthMock.mockReturnValue({
      initialized: true,
      isAuthenticated: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshSession: vi.fn(),
      reloadMe: vi.fn(),
      me: null
    });

    render(
      <MemoryRouter initialEntries={["/app/dashboard"]}>
        <AppRoutes />
      </MemoryRouter>
    );

    expect(await screen.findByRole("heading", { name: "Sign In" })).toBeInTheDocument();
  });
});
