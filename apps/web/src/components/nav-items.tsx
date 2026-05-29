import {
  Bell,
  Boxes,
  Building2,
  Gauge,
  LayoutDashboard,
  ListChecks,
  ShieldAlert,
  Store,
  Users,
  Workflow,
  Wrench
} from "lucide-react";
import * as React from "react";

export type NavItem = {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  requiredAny?: string[];
};

export const navItems: NavItem[] = [
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

export function hasAnyPermission(userPermissions: string[], requiredAny?: string[]) {
  if (!requiredAny?.length) return true;
  return requiredAny.some((permission) => userPermissions.includes(permission));
}
