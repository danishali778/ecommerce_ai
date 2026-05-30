import { Command, Menu, Search } from "lucide-react";

import { Button } from "@frontend/ui";

import { NotificationBell } from "@/components/notification-bell";
import { StoreSwitcher } from "@/components/store-switcher";
import { UserMenu } from "@/components/user-menu";
import { useAppState } from "@/hooks/use-app-state";

export function TopHeader() {
  const { setSidebarOpen } = useAppState();

  return (
    <div className="sticky top-0 z-30 border-b border-slate-200 bg-white/92 backdrop-blur-xl">
      <div className="px-4 py-3 sm:px-6 lg:px-8 xl:px-10">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex min-w-0 items-center gap-3">
            <Button variant="secondary" className="h-10 w-10 rounded-xl px-0 lg:hidden" onClick={() => setSidebarOpen(true)}>
              <Menu className="h-4 w-4" />
            </Button>

            <div className="min-w-0 flex-1 xl:min-w-[28rem]">
              <div className="relative rounded-2xl border border-slate-200 bg-slate-50 px-1.5 py-1.5">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  className="w-full rounded-[0.95rem] border border-transparent bg-transparent py-2.5 pl-11 pr-20 text-sm text-slate-900 outline-none transition placeholder:text-slate-400"
                  placeholder="Search orders, customers, SKUs, approvals, workflows..."
                />
                <span className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-400 sm:inline-flex">
                  <Command className="h-3 w-3" />
                  K
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-end xl:flex-nowrap">
            <StoreSwitcher />
            <div className="flex items-center gap-2.5">
              <NotificationBell />
              <UserMenu />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
