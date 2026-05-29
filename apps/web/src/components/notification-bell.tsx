import { useMutation, useQuery } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { Link } from "react-router-dom";

import { notificationsApi } from "@frontend/api-client";
import { Badge, Button, Card } from "@frontend/ui";

import { useAppState } from "@/hooks/use-app-state";

export function NotificationBell() {
  const { selectedStoreId } = useAppState();
  const { data, refetch } = useQuery({
    queryKey: ["notifications", "header", selectedStoreId],
    queryFn: () => notificationsApi.list({ status: "unread", store_id: selectedStoreId ?? undefined })
  });

  const markReadMutation = useMutation({
    mutationFn: (notificationId: string) => notificationsApi.markRead(notificationId),
    onSuccess: () => refetch()
  });

  const unread = data ?? [];

  return (
    <div className="relative">
      <details className="group">
        <summary className="list-none cursor-pointer">
          <span className="relative flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:border-accent-200 hover:bg-accent-50">
            <Bell className="h-4 w-4 text-slate-700" />
            {unread.length ? (
              <span className="absolute right-2 top-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-semibold text-white">
                {Math.min(unread.length, 9)}
              </span>
            ) : null}
          </span>
        </summary>
        <Card className="absolute right-0 z-20 mt-3 w-[25rem] overflow-hidden border-slate-200 p-0 shadow-soft">
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-slate-950">Unread notifications</p>
              <p className="text-xs text-slate-500">System updates, approvals, and workflow exceptions.</p>
            </div>
            <Button variant="ghost" className="px-2 py-1 text-xs" onClick={() => refetch()}>
              Refresh
            </Button>
          </div>
          <div className="max-h-[28rem] overflow-y-auto p-4">
            {unread.length ? (
              <div className="space-y-3">
                {unread.slice(0, 6).map((notification) => (
                  <div key={notification.id} className="rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-slate-950">{notification.title}</p>
                        <p className="mt-1 text-sm leading-6 text-slate-600">{notification.body}</p>
                      </div>
                      <Badge tone="warning">{notification.type.replaceAll("_", " ")}</Badge>
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      <p className="text-xs text-slate-400">{new Date(notification.created_at).toLocaleString()}</p>
                      <Button
                        variant="ghost"
                        className="px-0 py-0 text-xs text-accent-600"
                        onClick={() => markReadMutation.mutate(notification.id)}
                      >
                        Mark read
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500">
                No unread notifications for the current workspace.
              </div>
            )}
          </div>
          <div className="border-t border-slate-200 px-4 py-3">
            <Link to="/app/notifications" className="text-sm font-medium text-accent-600">
              Open notification center
            </Link>
          </div>
        </Card>
      </details>
    </div>
  );
}
