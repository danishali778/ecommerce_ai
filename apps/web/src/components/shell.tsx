import * as React from "react";
import {
  Bell,
  Boxes,
  Building2,
  Gauge,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Search,
  Settings2,
  ShieldAlert,
  Store,
  Users,
  Workflow,
  Wrench
} from "lucide-react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";

import { notificationsApi } from "@frontend/api-client";
import { Badge, Button, Card, Select, cn } from "@frontend/ui";

import { useAppState } from "@/app/use-app-state";
import { useAuth } from "@/app/use-auth";

type NavItem = {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  requiredAny?: string[];
};

const navItems: NavItem[] = [
  { to: "/app/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/app/stores", label: "Stores", icon: Store, requiredAny: ["stores.manage", "sync.read"] },
  { to: "/app/catalog", label: "Catalog", icon: Boxes, requiredAny: ["catalog.read"] },
  { to: "/app/approvals", label: "Approvals", icon: ListChecks, requiredAny: ["approvals.read"] },
  { to: "/app/support", label: "Support", icon: Wrench, requiredAny: ["support.read"] },
  { to: "/app/fraud", label: "Fraud", icon: ShieldAlert, requiredAny: ["fraud.read"] },
  { to: "/app/inventory", label: "Inventory", icon: Boxes, requiredAny: ["inventory.read"] },
  { to: "/app/analytics", label: "Analytics", icon: Gauge, requiredAny: ["analytics.read"] },
  { to: "/app/notifications", label: "Notifications", icon: Bell, requiredAny: ["notifications.read"] },
  { to: "/app/organization", label: "Organization", icon: Building2, requiredAny: ["org.manage"] },
  { to: "/app/users", label: "Users", icon: Users, requiredAny: ["users.manage"] },
  { to: "/app/runtime/workflows", label: "Runtime", icon: Workflow, requiredAny: ["logs.read"] }
];

function hasAnyPermission(userPermissions: string[], requiredAny?: string[]) {
  if (!requiredAny?.length) return true;
  return requiredAny.some((permission) => userPermissions.includes(permission));
}

export function PublicShell({ children }: React.PropsWithChildren) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(21,88,214,0.09),transparent_40%),linear-gradient(to_bottom,#f8fbff,#f8fafc)]">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/85 backdrop-blur">
        <div className="app-container flex items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-3 text-2xl font-semibold tracking-tight text-slate-950">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-accent-50 text-accent-700 shadow-sm">
              <LayoutDashboard className="h-5 w-5" />
            </span>
            CommerceOps AI
          </Link>
          <nav className="hidden items-center gap-8 text-sm text-slate-600 md:flex">
            <a href="#features">Features</a>
            <a href="#process">Process</a>
            <a href="#safety">Safety</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-medium text-accent-600">
              Log In
            </Link>
            <Link to="/signup">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>
      {children}
    </div>
  );
}

function StoreSwitcher() {
  const { me } = useAuth();
  const { selectedStoreId, setSelectedStoreId } = useAppState();
  const navigate = useNavigate();
  const location = useLocation();
  const stores = me?.accessible_stores ?? [];

  if (!stores.length) return null;

  const onChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const next = event.target.value;
    setSelectedStoreId(next);

    if (location.pathname.startsWith("/app/stores/")) {
      navigate(`/app/stores/${next}`);
      return;
    }
    if (location.pathname.startsWith("/app/catalog/")) {
      navigate(`/app/catalog/${next}/products`);
      return;
    }
    if (location.pathname.startsWith("/app/support/")) {
      navigate(`/app/support/${next}/conversations`);
      return;
    }
    if (location.pathname.startsWith("/app/fraud/")) {
      navigate(`/app/fraud/${next}/reviews`);
      return;
    }
    if (location.pathname.startsWith("/app/inventory/")) {
      navigate(`/app/inventory/${next}`);
      return;
    }
    if (location.pathname.startsWith("/app/analytics/")) {
      navigate(`/app/analytics/${next}`);
      return;
    }
    if (location.pathname.startsWith("/app/runtime/")) {
      navigate(`/app/runtime/workflows/${next}`);
    }
  };

  return (
    <div className="min-w-56">
      <Select value={selectedStoreId ?? stores[0].id} onChange={onChange}>
        {stores.map((store) => (
          <option key={store.id} value={store.id}>
            {store.name}
          </option>
        ))}
      </Select>
    </div>
  );
}

function NotificationBell() {
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

function Sidebar() {
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

function TopHeader() {
  const { me, logout } = useAuth();
  const navigate = useNavigate();

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
          <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
            <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-slate-100 text-xs font-semibold text-slate-700">
              {me?.user.full_name
                ?.split(/\s+/)
                .slice(0, 2)
                .map((part) => part[0])
                .join("")
                .toUpperCase() ?? "U"}
            </span>
            <div className="hidden text-left sm:block">
              <p className="text-sm font-medium text-slate-900">{me?.user.full_name ?? "User"}</p>
              <p className="text-xs text-slate-500">{me?.roles.join(", ") || "Operator"}</p>
            </div>
            <Button
              variant="ghost"
              className="px-2"
              onClick={async () => {
                await logout();
                navigate("/login");
              }}
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="min-h-screen flex-1">
        <TopHeader />
        <main className="app-container px-6 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
