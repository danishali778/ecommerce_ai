import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@frontend/ui";

import { useAuth } from "@/hooks/use-auth";

export function UserMenu() {
  const { me, logout } = useAuth();
  const navigate = useNavigate();

  return (
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
  );
}
