import * as React from "react";
import { LayoutDashboard, X } from "lucide-react";
import { Link, NavLink, useLocation } from "react-router-dom";

import { Button, Drawer, cn } from "@frontend/ui";

import { hasAnyPermission, navItems } from "@/components/nav-items";
import { useAppState } from "@/hooks/use-app-state";
import { useAuth } from "@/hooks/use-auth";

function SidebarContent({ mobile, onNavigate }: { mobile?: boolean; onNavigate?: () => void }) {
  const { me } = useAuth();
  const permissions = me?.permissions ?? [];
  const visibleItems = navItems.filter((item) => hasAnyPermission(permissions, item.requiredAny));

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-start justify-between gap-4 border-b border-slate-200 pb-5">
        <Link to="/app/dashboard" className="flex items-center gap-3 text-xl font-semibold tracking-tight text-slate-950" onClick={onNavigate}>
          <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-accent-700">
            <LayoutDashboard className="h-5 w-5" />
          </span>
          <span className="space-y-1">
            <span className="block text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400">CommerceOps</span>
            <span className="block text-[1.45rem] leading-none text-slate-950">AI</span>
          </span>
        </Link>
        {mobile ? (
          <Button variant="ghost" className="h-10 w-10 rounded-xl px-0" onClick={onNavigate}>
            <X className="h-4 w-4" />
          </Button>
        ) : null}
      </div>

      <div className="mt-5">
        <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">Navigation</p>
      </div>
      <nav className="mt-3 space-y-1">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.label}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-xl px-2.5 py-2.5 text-sm font-medium transition duration-200",
                  isActive
                    ? "bg-accent-50 text-slate-950"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                )
              }
            >
              <span
                className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-transparent transition",
                  "group-hover:border-slate-200 group-hover:bg-white"
                )}
              >
                <Icon className="h-4 w-4 shrink-0 text-slate-500" />
              </span>
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}

export function SidebarNav() {
  const { sidebarOpen, setSidebarOpen } = useAppState();
  const location = useLocation();

  React.useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname, setSidebarOpen]);

  return (
    <>
      <aside className="hidden h-screen w-[16rem] shrink-0 overflow-y-auto border-r border-slate-200 bg-white px-4 py-5 scrollbar-hidden lg:block">
        <SidebarContent />
      </aside>

      <Drawer open={sidebarOpen} onClose={() => setSidebarOpen(false)}>
        <div className="lg:hidden">
          <SidebarContent mobile onNavigate={() => setSidebarOpen(false)} />
        </div>
      </Drawer>
    </>
  );
}
