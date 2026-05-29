import { LayoutDashboard, Settings2 } from "lucide-react";
import { Link, NavLink } from "react-router-dom";

import { Badge } from "@frontend/ui";

import { hasAnyPermission, navItems } from "@/components/nav-items";
import { useAppState } from "@/hooks/use-app-state";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@frontend/ui";

export function SidebarNav() {
  const { sidebarOpen } = useAppState();
  const { me } = useAuth();
  if (!sidebarOpen) return null;

  const permissions = me?.permissions ?? [];
  const visibleItems = navItems.filter((item) => hasAnyPermission(permissions, item.requiredAny));

  return (
    <aside className="hidden min-h-screen w-80 shrink-0 border-r border-slate-200 bg-white px-5 py-6 lg:flex lg:flex-col">
      <Link to="/app/dashboard" className="flex items-center gap-3 text-2xl font-semibold tracking-tight text-slate-950">
        <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-accent-50 text-accent-700 shadow-sm">
          <LayoutDashboard className="h-5 w-5" />
        </span>
        CommerceOps AI
      </Link>
      <p className="mt-2 text-sm text-slate-500">Internal commerce operations</p>

      <nav className="mt-8 space-y-1">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition",
                  isActive ? "bg-accent-50 text-accent-700 shadow-sm" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      <div className="mt-auto space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white shadow-sm">
            <Settings2 className="h-4 w-4 text-slate-700" />
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-900">System operational</p>
            <p className="text-xs text-slate-500">Sync, workflows, and APIs responding normally.</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 text-xs text-slate-500">
          <Badge tone="success">Live</Badge>
          <Badge tone="neutral">{me?.organization?.name ?? "No organization"}</Badge>
        </div>
      </div>
    </aside>
  );
}
