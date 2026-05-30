import { useMutation, useQuery } from "@tanstack/react-query";
import { Bell, Sparkles } from "lucide-react";
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
          <span className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white transition hover:border-accent-200 hover:bg-accent-50/40">
            <Bell className="h-4 w-4 text-slate-700" />
            {unread.length ? (
              <span className="absolute right-2 top-2 flex h-5 min-w-5 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-semibold text-white shadow-sm">
                {Math.min(unread.length, 9)}
              </span>
            ) : null}
          </span>
        </summary>
        <Card className="absolute right-0 z-20 mt-3 w-[24rem] max-w-[calc(100vw-1rem)] overflow-hidden border-slate-200 p-0 shadow-[0_24px_70px_rgba(15,23,42,0.14)] max-sm:right-[-4rem]">
          <div className="border-b border-slate-200 bg-[linear-gradient(135deg,rgba(255,255,255,0.98),rgba(239,246,255,0.92))] px-4 py-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-white/90 bg-white/90 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-accent-700 shadow-sm">
                  <Sparkles className="h-3 w-3" />
                  Notifications
                </div>
                <p className="mt-3 text-sm font-semibold text-slate-950">Unread notifications</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">System updates, approvals, and workflow exceptions for the current workspace.</p>
              </div>
              <Button variant="ghost" className="px-2 py-1 text-xs" onClick={() => refetch()}>
                Refresh
              </Button>
            </div>
          </div>
          <div className="max-h-[28rem] overflow-y-auto bg-slate-50/70 p-4 scrollbar-hidden">
            {unread.length ? (
              <div className="space-y-3">
                {unread.slice(0, 6).map((notification) => (
                  <div key={notification.id} className="rounded-[1.35rem] border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-slate-950">{notification.title}</p>
                        <p className="mt-1 text-sm leading-6 text-slate-600">{notification.body}</p>
                      </div>
                      <Badge tone="warning">{notification.type.replaceAll("_", " ")}</Badge>
                    </div>
                    <div className="mt-3 flex items-center justify-between gap-3">
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
              <div className="rounded-[1.35rem] border border-dashed border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
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
