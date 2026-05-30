import * as React from "react";
import { LayoutDashboard } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@frontend/ui";

export function PublicShell({ children }: React.PropsWithChildren) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(21,88,214,0.09),transparent_40%),linear-gradient(to_bottom,#f8fbff,#f8fafc)]">
      <header className="sticky top-4 z-40 mx-auto max-w-7xl px-4 sm:px-6">
        <div className="rounded-3xl border border-white/70 bg-white/75 px-5 shadow-soft backdrop-blur-xl transition-all duration-300 hover:bg-white/90">
          <div className="flex items-center justify-between gap-3 py-3">
            <Link to="/" className="group flex min-w-0 items-center gap-3 text-xl font-semibold tracking-tight text-slate-950 sm:text-2xl">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-accent-50 text-accent-600 shadow-sm transition-all duration-300 group-hover:scale-105 group-hover:bg-accent-500 group-hover:text-white group-hover:rotate-6">
                <LayoutDashboard className="h-5 w-5" />
              </span>
              <span className="truncate bg-gradient-to-r from-slate-950 to-slate-800 bg-clip-text font-bold text-slate-900 group-hover:text-accent-600 transition-colors duration-200">
                CommerceOps
                <span className="text-accent-500 font-medium"> AI</span>
              </span>
            </Link>

            <div className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex">
              <a href="#features" className="transition-colors duration-200 hover:text-accent-600">Features</a>
              <a href="#process" className="transition-colors duration-200 hover:text-accent-600">Process</a>
              <a href="#safety" className="transition-colors duration-200 hover:text-accent-600">Safety</a>
            </div>

            <div className="flex shrink-0 items-center gap-3 sm:gap-4">
              <Link to="/login" className="text-sm font-semibold text-slate-600 hover:text-accent-600 transition-colors duration-200 max-sm:hidden">
                Log In
              </Link>
              <Link to="/signup">
                <Button className="rounded-2xl bg-accent-500 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-500/10 transition-all duration-300 hover:-translate-y-0.5 hover:bg-accent-600 hover:shadow-lg hover:shadow-accent-500/20 active:translate-y-0">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 border-t border-slate-200/50 py-2.5 md:hidden">
            <nav className="flex min-w-0 flex-1 items-center gap-2 overflow-x-auto scrollbar-hidden text-xs text-slate-600">
              <a className="whitespace-nowrap rounded-full border border-slate-200 bg-white px-3.5 py-1.5 font-medium transition-colors hover:bg-white hover:text-accent-600" href="#features">
                Features
              </a>
              <a className="whitespace-nowrap rounded-full border border-slate-200 bg-white px-3.5 py-1.5 font-medium transition-colors hover:bg-white hover:text-accent-600" href="#process">
                Process
              </a>
              <a className="whitespace-nowrap rounded-full border border-slate-200 bg-white px-3.5 py-1.5 font-medium transition-colors hover:bg-white hover:text-accent-600" href="#safety">
                Safety
              </a>
            </nav>
            <Link to="/login" className="shrink-0 text-xs font-semibold text-accent-600 px-2 hover:text-accent-700">
              Log In
            </Link>
          </div>
        </div>
      </header>
      {children}
    </div>
  );
}
