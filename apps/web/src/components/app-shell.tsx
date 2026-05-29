import { Outlet } from "react-router-dom";

import { SidebarNav } from "@/components/sidebar-nav";
import { TopHeader } from "@/components/top-header";

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <SidebarNav />
      <div className="min-h-screen flex-1">
        <TopHeader />
        <main className="app-container px-6 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
