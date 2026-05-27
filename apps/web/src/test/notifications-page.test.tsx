import { fireEvent, screen, waitFor } from "@testing-library/react";

import { NotificationsPage } from "@/pages";
import { renderWithProviders } from "@/test/utils";

const listMock = vi.fn();
const markReadMock = vi.fn();

vi.mock("@frontend/api-client", async () => {
  const actual = await vi.importActual<object>("@frontend/api-client");
  return {
    ...actual,
    notificationsApi: {
      list: (...args: unknown[]) => listMock(...args),
      markRead: (...args: unknown[]) => markReadMock(...args)
    }
  };
});

describe("notifications page", () => {
  beforeEach(() => {
    listMock.mockResolvedValue([
      {
        id: "notif-1",
        type: "sync_failed",
        channel: "in_app",
        title: "Sync failed",
        body: "Order sync failed for one record.",
        status: "unread",
        created_at: "2026-05-26T10:00:00.000Z",
        read_at: null
      }
    ]);
    markReadMock.mockResolvedValue({
      id: "notif-1",
      status: "read"
    });
  });

  it("marks unread notifications as read", async () => {
    renderWithProviders(<NotificationsPage />, { route: "/app/notifications", path: "/app/notifications" });

    expect(await screen.findByText("Sync failed")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Mark as read" }));

    await waitFor(() => {
      expect(markReadMock).toHaveBeenCalledWith("notif-1");
    });
  });
});
