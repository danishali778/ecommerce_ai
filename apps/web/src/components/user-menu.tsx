import { LogOut, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@frontend/ui";

import { useAuth } from "@/hooks/use-auth";

export function UserMenu() {
  const { me, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-2.5 py-2">
      <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-xs font-semibold text-slate-800">
        {me?.user.full_name
          ?.split(/\s+/)
          .slice(0, 2)
          .map((part) => part[0])
          .join("")
          .toUpperCase() ?? "U"}
      </span>
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold text-slate-900">{me?.user.full_name ?? "User"}</p>
        <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
          <span className="truncate">{me?.roles.join(", ") || "Operator"}</span>
        </div>
      </div>
      <div className="flex items-center gap-2 pl-1">
        <Button
          variant="ghost"
          className="h-8 w-8 rounded-lg px-0"
          onClick={async () => {
            await logout();
            navigate("/login");
          }}
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
