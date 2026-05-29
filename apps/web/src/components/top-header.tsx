import { Search } from "lucide-react";

import { StoreSwitcher } from "@/components/store-switcher";
import { NotificationBell } from "@/components/notification-bell";
import { UserMenu } from "@/components/user-menu";

export function TopHeader() {
  return (
    <div className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 px-6 py-4 backdrop-blur">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="relative w-full lg:max-w-xl">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-sm outline-none transition focus:border-accent-300 focus:bg-white focus:ring-4 focus:ring-accent-100"
            placeholder="Search orders, customers, SKUs, approvals, workflows..."
          />
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <StoreSwitcher />
          <NotificationBell />
          <UserMenu />
        </div>
      </div>
    </div>
  );
}
