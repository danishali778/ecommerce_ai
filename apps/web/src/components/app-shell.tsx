import { Outlet } from "react-router-dom";

import { SidebarNav } from "@/components/sidebar-nav";
import { TopHeader } from "@/components/top-header";

export function AppShell() {
  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#f6f8fc_0%,#f8fafc_18%,#f5f7fb_100%)]">
      <div className="mx-auto flex min-h-screen w-full max-w-[1920px] lg:h-screen lg:overflow-hidden">
        <SidebarNav />
        <div className="min-h-screen min-w-0 flex-1 lg:h-screen lg:overflow-y-auto lg:scrollbar-hidden">
          <TopHeader />
          <main className="px-4 pb-12 pt-6 sm:px-6 lg:px-8 xl:px-10">
            <div className="app-container min-w-0">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
