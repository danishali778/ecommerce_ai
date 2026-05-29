import { LayoutDashboard } from "lucide-react";
import { Link } from "react-router-dom";
import * as React from "react";

import { Button } from "@frontend/ui";

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
