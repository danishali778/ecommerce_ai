import * as React from "react";
import { ArrowRight, BadgeCheck, BellRing, Boxes, ChartColumnBig, LayoutDashboard, ListChecks, ShieldCheck, Sparkles, Workflow, Wrench } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Button, Card, Input, PasswordInput } from "@frontend/ui";

import { useAuth } from "@/hooks/use-auth";

function MarketingSection({
  id,
  eyebrow,
  title,
  copy,
  children
}: React.PropsWithChildren<{ id?: string; eyebrow?: string; title: string; copy: string }>) {
  return (
    <section id={id} className="app-container scroll-mt-32 px-4 py-20 sm:px-6 md:py-24">
      <div className="max-w-3xl">
        {eyebrow ? (
          <div className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-600 shadow-sm backdrop-blur-sm">
            {eyebrow}
          </div>
        ) : null}
        <h2 className="mt-6 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl md:text-5xl leading-[1.1]">{title}</h2>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-slate-600 sm:text-lg">{copy}</p>
      </div>
      <div className="mt-12 sm:mt-16">{children}</div>
    </section>
  );
}

export function LandingPage() {
  const navItems = [
    { label: "Dashboard", active: true },
    { label: "Catalog", active: false },
    { label: "Approvals", active: false },
    { label: "Support", active: false },
    { label: "Fraud", active: false },
    { label: "Inventory", active: false }
  ];

  const featureCards = [
    { icon: Boxes, title: "Catalog drafts", body: "Generate SEO and product copy drafts, review them, and submit them into approval workflows." },
    { icon: ListChecks, title: "Approval workflows", body: "Keep risky or customer-facing changes behind explicit human approval and execution states." },
    { icon: Wrench, title: "Support workspace", body: "Review grounded support drafts with policy citations, order facts, and customer context." },
    { icon: ShieldCheck, title: "Fraud review", body: "Inspect surfaced risk cases with deterministic signals and decision-support context." },
    { icon: Workflow, title: "Inventory follow-up", body: "Track low-stock alerts and manage supplier communication as reviewable drafts." },
    { icon: ChartColumnBig, title: "Traceable analytics", body: "Monitor workflow activity, performance trends, and operational exceptions." }
  ];

  return (
    <div className="pb-16">
      <section className="app-container grid gap-12 px-4 pb-16 pt-12 sm:px-6 sm:pb-20 sm:pt-16 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:items-center lg:gap-16 lg:pb-24 lg:pt-28">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-accent-100 bg-accent-50/50 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-accent-700 shadow-sm backdrop-blur-sm">
            <Sparkles className="h-3.5 w-3.5 text-accent-500 animate-pulse" />
            AI-Assisted Operations with Human Review
          </div>
          <h1 className="mt-8 max-w-3xl text-4xl font-extrabold tracking-tight text-slate-950 sm:text-5xl sm:leading-[1.1] lg:text-6xl leading-[1.05]">
            AI-Powered Shopify Operations.{" "}
            <span className="relative inline-block text-accent-600">
              <span className="relative z-10 bg-gradient-to-r from-accent-600 via-accent-500 to-accent-700 bg-clip-text text-transparent">Human-Controlled Execution.</span>
              <span className="absolute bottom-1 left-0 h-1.5 w-full bg-accent-100/60 rounded-full -z-10" />
            </span>
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-relaxed text-slate-600 sm:text-lg sm:leading-loose">
            CommerceOps AI bridges the gap between machine intelligence and merchant trust. Connect your Shopify store to generate high-quality product copy, draft support responses, manage suppliers, and execute risk decisions with full human oversight.
          </p>
          <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-center">
            <Link to="/signup" className="group">
              <Button className="w-full gap-2.5 rounded-2xl bg-accent-500 px-7 py-4 text-base font-semibold text-white shadow-xl shadow-accent-500/20 transition-all duration-300 hover:-translate-y-1 hover:bg-accent-600 hover:shadow-2xl hover:shadow-accent-500/35 active:translate-y-0 sm:w-auto">
                Get Started
                <ArrowRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" />
              </Button>
            </Link>
            <a href="#process">
              <Button variant="secondary" className="w-full rounded-2xl border border-slate-200 bg-white px-7 py-4 text-base font-semibold text-slate-700 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:bg-slate-50 active:translate-y-0 sm:w-auto">
                See How It Works
              </Button>
            </a>
          </div>
          <div className="mt-10 flex flex-wrap gap-4 text-xs font-semibold text-slate-600">
            <span className="inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-white/60 px-4 py-2 shadow-sm backdrop-blur-sm">
              <ShieldCheck className="h-4 w-4 text-emerald-500" />
              Zero Black-Box Actions
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-white/60 px-4 py-2 shadow-sm backdrop-blur-sm">
              <ListChecks className="h-4 w-4 text-accent-500" />
              100% Auditable History
            </span>
          </div>
        </div>

        <Card className="mx-auto w-full max-w-[46rem] overflow-hidden rounded-[2.5rem] border border-accent-100/70 bg-white/95 shadow-soft lg:mx-0 lg:max-w-none transition-all duration-300 hover:shadow-2xl">
          <div className="flex flex-col gap-3 border-b border-slate-100 bg-slate-50/70 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-full bg-slate-300/80" />
              <span className="h-3 w-3 rounded-full bg-slate-300/80" />
              <span className="h-3 w-3 rounded-full bg-slate-300/80" />
              <span className="ml-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Operator Console v1.0</span>
            </div>
            <div className="w-full max-w-[15rem] rounded-xl border border-slate-200 bg-white px-4 py-1.5 text-[11px] text-slate-400 shadow-inner">
              Search orders, drafts, audit logs...
            </div>
          </div>
          
          <div className="grid min-h-[36rem] grid-cols-1 md:grid-cols-[14rem_minmax(0,1fr)]">
            <div className="border-b border-slate-100 bg-slate-50/30 p-5 md:border-b-0 md:border-r">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-1">
                {[
                  { label: "Dashboard", icon: LayoutDashboard, active: true },
                  { label: "Catalog Drafts", icon: Boxes, active: false },
                  { label: "Approvals", icon: ListChecks, active: false },
                  { label: "Support Room", icon: Wrench, active: false },
                  { label: "Fraud Review", icon: ShieldCheck, active: false },
                  { label: "Inventory Sync", icon: Workflow, active: false }
                ].map(({ label, icon: Icon, active }) => (
                  <div
                    key={label}
                    className={`flex items-center gap-3 rounded-xl px-4 py-3 text-xs font-semibold transition-all duration-200 cursor-pointer ${
                      active 
                        ? "bg-accent-50 text-accent-700 shadow-sm border border-accent-100/50" 
                        : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
                    }`}
                  >
                    <Icon className={`h-4 w-4 ${active ? "text-accent-500" : "text-slate-400"}`} />
                    {label}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="space-y-6 bg-white p-6">
              <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
                {[
                  ["Sync Status", "Healthy", "text-emerald-600 bg-emerald-50/70 border-emerald-100"],
                  ["Approvals", "15 Pending", "text-accent-700 bg-accent-50/70 border-accent-100"],
                  ["Support Drafts", "12 Ready", "text-slate-600 bg-slate-50/70 border-slate-150"],
                  ["Stock Alerts", "5 Critical", "text-rose-600 bg-rose-50/70 border-rose-100"]
                ].map(([label, value, styles]) => (
                  <div key={label} className={`rounded-2xl border p-4 shadow-sm transition-all duration-200 hover:shadow-md cursor-pointer ${styles.split(' ')[2] || ''}`}>
                    <p className="text-[9px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
                    <p className={`mt-2 text-sm font-bold truncate ${styles.split(' ')[0]}`}>{value}</p>
                  </div>
                ))}
              </div>

              <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded-3xl border border-accent-100 bg-gradient-to-b from-accent-50/30 to-white p-5 shadow-sm">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-bold text-slate-900">AI Recommendation</p>
                      <p className="text-[10px] text-slate-500">Shopify Risk Mitigation</p>
                    </div>
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-[9px] font-bold text-amber-700 border border-amber-100">
                      <ShieldCheck className="h-3 w-3 text-amber-600" /> Review Needed
                    </span>
                  </div>

                  <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-inner">
                    <div className="flex items-center gap-2">
                      <span className="flex h-5 w-5 items-center justify-center rounded bg-rose-50 text-rose-500 font-bold text-xs">!</span>
                      <p className="text-xs font-bold text-slate-900">Fraud Risk Hold (Order #1048)</p>
                    </div>
                    <p className="mt-3 text-[11px] leading-relaxed text-slate-600">
                      Shipping address changed from <span className="font-semibold text-slate-800">NY, USA</span> to <span className="font-semibold text-slate-800">Lagos, Nigeria</span> 4 minutes post-checkout. Fulfillment hold recommended.
                    </p>
                    
                    <div className="mt-4 grid grid-cols-2 gap-2">
                      <button className="flex h-9 items-center justify-center rounded-xl bg-accent-500 text-[10px] font-bold text-white shadow-md shadow-accent-500/10 hover:bg-accent-600 hover:shadow-lg transition-all">
                        Hold Fulfillment
                      </button>
                      <button className="flex h-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-[10px] font-bold text-slate-600 hover:bg-slate-50 transition-colors">
                        Approve Order
                      </button>
                    </div>
                  </div>
                </div>

                <div className="rounded-3xl border border-slate-100 bg-slate-50/50 p-5 shadow-sm">
                  <p className="text-xs font-bold text-slate-900">Recent Action Log</p>
                  <div className="mt-4 space-y-4">
                    {[
                      { initial: "JD", action: "approved SEO Copy Draft", target: "Silk Slip Dress", color: "bg-accent-100 text-accent-700" },
                      { initial: "Sys", action: "synced inventory levels", target: "12 active items", color: "bg-slate-200 text-slate-700" },
                      { initial: "MK", action: "approved refund request", target: "Ticket #4108", color: "bg-emerald-100 text-emerald-700" }
                    ].map(({ initial, action, target, color }, idx) => (
                      <div key={idx} className="flex gap-3 items-start">
                        <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-lg font-bold text-[9px] ${color}`}>
                          {initial}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-[11px] leading-snug text-slate-700">
                            <span className="font-semibold text-slate-900">{initial === "Sys" ? "System" : `Operator ${initial}`}</span> {action}
                          </p>
                          <p className="mt-0.5 text-[9px] font-medium text-slate-400 truncate">{target}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </section>

      <MarketingSection
        id="features"
        eyebrow="Core capabilities"
        title="One control plane for high-velocity commerce work"
        copy="Coordinate deterministic workflows and AI-assisted drafting from one operational surface built for internal teams."
      >
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {featureCards.map(({ icon: Icon, title, body }) => (
            <Card 
              key={title} 
              className="group h-full rounded-[2rem] border border-slate-100 bg-white/70 p-8 shadow-sm backdrop-blur-sm cursor-pointer transition-all duration-300 hover:-translate-y-2 hover:bg-white hover:border-accent-100 hover:shadow-lg"
            >
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-50 text-accent-600 shadow-sm transition-all duration-300 group-hover:scale-110 group-hover:bg-accent-500 group-hover:text-white group-hover:shadow-md group-hover:shadow-accent-500/10">
                <Icon className="h-5 w-5" />
              </span>
              <h3 className="mt-6 text-lg font-bold text-slate-900 group-hover:text-accent-600 transition-colors duration-200">{title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-slate-600">{body}</p>
            </Card>
          ))}
        </div>
      </MarketingSection>

      <MarketingSection
        id="process"
        eyebrow="Workflow"
        title="Connect, sync, draft, review, execute"
        copy="CommerceOps AI keeps the operational loop visible from ingestion to human review to audited execution."
      >
        <div className="relative grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          {[
            ["01", "Connect Store", "Link Shopify securely, configure roles, and bootstrap sync access."],
            ["02", "Sync Context", "Ingest products, orders, customers, stock levels, and alerts in near real-time."],
            ["03", "AI-Draft Actions", "Prepare premium product copy, grounded support responses, and supplier drafts."],
            ["04", "Safe Review", "Execute updates through auditable approval steps and human-in-the-loop validation."]
          ].map(([num, title, body], idx) => (
            <Card 
              key={title} 
              className="relative overflow-hidden h-full rounded-[2rem] border border-slate-100 bg-white/70 p-8 shadow-sm cursor-pointer transition-all duration-300 hover:-translate-y-1.5 hover:bg-white hover:border-accent-100 hover:shadow-lg"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-black tracking-widest text-accent-500 bg-accent-50/70 border border-accent-100 px-3 py-1 rounded-xl shadow-inner">
                  {num}
                </span>
                {idx < 3 && (
                  <span className="hidden xl:block absolute top-[2.5rem] right-[-1.5rem] text-slate-350 font-normal text-xl z-10 select-none">
                    →
                  </span>
                )}
              </div>
              <h3 className="mt-6 text-lg font-bold text-slate-900">{title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-slate-600">{body}</p>
            </Card>
          ))}
        </div>
      </MarketingSection>

      <MarketingSection
        id="safety"
        eyebrow="Trust and safety"
        title="AI assistance with clear human accountability"
        copy="The platform is designed so operators stay in control. Recommendations are visible, statuses are explicit, and execution remains traceable."
      >
        <div className="grid gap-6 md:grid-cols-2">
          <Card className="h-full rounded-[2.25rem] border border-slate-100 bg-white/70 p-8 shadow-sm transition-all duration-300 hover:shadow-lg hover:border-emerald-100">
            <div className="flex items-center gap-4">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 shadow-sm">
                <BadgeCheck className="h-6 w-6" />
              </span>
              <p className="text-xl font-bold text-slate-900">Human-Controlled Execution</p>
            </div>
            <p className="mt-5 text-sm leading-relaxed text-slate-600">
              No black-box mutations. AI never auto-approves description changes, sends customer support replies silently, or mutates high-risk Shopify fulfillment states. An operator stays central to every action.
            </p>
          </Card>
          
          <Card className="h-full rounded-[2.25rem] border border-slate-100 bg-white/70 p-8 shadow-sm transition-all duration-300 hover:shadow-lg hover:border-accent-100">
            <div className="flex items-center gap-4">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-50 text-accent-600 shadow-sm">
                <BellRing className="h-6 w-6" />
              </span>
              <p className="text-xl font-bold text-slate-900">Traceability by Default</p>
            </div>
            <p className="mt-5 text-sm leading-relaxed text-slate-600">
              Complete observability into all automation states. Step-by-step workflow runs, detailed agent outputs, interactive notifications, and an immutable audit registry make it easy to explain exactly what happened and why.
            </p>
          </Card>
        </div>
      </MarketingSection>

      <section className="app-container px-4 py-20 sm:px-6 md:py-24">
        <Card className="relative overflow-hidden rounded-[2.5rem] border border-white/10 bg-[radial-gradient(circle_at_top_right,rgba(21,88,214,0.18),transparent_50%),linear-gradient(to_bottom,#0f172a,#020617)] p-8 text-white shadow-soft sm:p-12 lg:p-16">
          <div className="relative z-10 grid gap-10 xl:grid-cols-[1fr_auto] xl:items-center">
            <div className="space-y-6">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-accent-500/30 bg-accent-500/10 px-3.5 py-1.5 text-[10px] font-bold uppercase tracking-[0.2em] text-accent-300 shadow-sm backdrop-blur-sm">
                Ready to Experience the Difference?
              </span>
              <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl md:text-5xl leading-[1.1] max-w-3xl">
                Bring storefront operations under one secure, reviewable workspace.
              </h2>
              <p className="max-w-2xl text-sm leading-relaxed text-slate-300 sm:text-base">
                Link your storefront syncs, structure approvals, and coordinate team review. Empower operations with human-controlled intelligence.
              </p>
            </div>
            
            <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:gap-4">
              <Link to="/signup" className="group">
                <Button className="w-full gap-2 rounded-2xl bg-white px-7 py-4 text-base font-semibold text-slate-950 shadow-lg shadow-white/5 transition-all duration-300 hover:-translate-y-1 hover:bg-slate-100 hover:shadow-xl sm:w-auto">
                  Create Account
                  <ArrowRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" />
                </Button>
              </Link>
              <a href="#features">
                <Button variant="ghost" className="w-full rounded-2xl border border-white/10 bg-white/5 px-7 py-4 text-base font-semibold text-white transition-all duration-300 hover:-translate-y-1 hover:bg-white/10 sm:w-auto">
                  Explore Features
                </Button>
              </a>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}

function AuthFormShell({
  title,
  copy,
  children,
  asideTitle,
  asideCopy,
  asideContent
}: React.PropsWithChildren<{
  title: string;
  copy: string;
  asideTitle: string;
  asideCopy: string;
  asideContent: React.ReactNode;
}>) {
  return (
    <div className="app-container grid min-h-[calc(100vh-80px)] gap-0 px-4 py-10 sm:px-6 sm:py-12 lg:grid-cols-[1fr_1fr]">
      <div className="rounded-t-[2rem] bg-[#eef3ff] p-8 lg:rounded-l-[2rem] lg:rounded-tr-none lg:p-10">
        <h2 className="text-4xl font-semibold tracking-tight text-slate-950">{asideTitle}</h2>
        <p className="mt-5 max-w-xl text-base leading-8 text-slate-600">{asideCopy}</p>
        <div className="mt-12">{asideContent}</div>
      </div>
      <div className="rounded-b-[2rem] border border-slate-200 bg-white p-8 lg:rounded-r-[2rem] lg:rounded-bl-none lg:p-16">
        <div className="mx-auto max-w-lg">
          <h1 className="text-4xl font-semibold tracking-tight text-slate-950">{title}</h1>
          <p className="mt-4 text-sm leading-7 text-slate-600">{copy}</p>
          <div className="mt-10">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login({ email, password });
      const next = (location.state as { from?: string } | null)?.from ?? "/app/dashboard";
      navigate(next, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthFormShell
      title="Sign In"
      copy="Welcome back. Enter your credentials to access your internal operations workspace."
      asideTitle="Human-Supervised Shopify Operations"
      asideCopy="Run sync, approvals, support, fraud review, and inventory follow-up from one operational console while keeping your team in control."
      asideContent={
        <Card className="overflow-hidden border-slate-200 bg-slate-950">
          <div className="h-[28rem] bg-[radial-gradient(circle_at_top,rgba(21,88,214,0.35),transparent_50%),linear-gradient(to_bottom,#0f172a,#111827)] p-6">
            <div className="flex h-full flex-col rounded-2xl border border-white/10 bg-slate-900/60 p-5">
              <div className="flex items-center justify-between">
                <span className="h-3 w-3 rounded-full bg-slate-400" />
                <div className="h-8 w-40 rounded-xl bg-white/10" />
              </div>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div className="h-24 rounded-2xl bg-white/10" />
                <div className="h-24 rounded-2xl bg-white/10" />
              </div>
              <div className="mt-6 flex-1 rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="h-4 w-44 rounded bg-white/10" />
                <div className="mt-4 space-y-3">
                  <div className="h-10 rounded-xl bg-accent-500/70" />
                  <div className="h-10 rounded-xl bg-white/10" />
                  <div className="h-10 rounded-xl bg-white/10" />
                </div>
              </div>
            </div>
          </div>
        </Card>
      }
    >
      <form className="space-y-5" onSubmit={onSubmit}>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">Email address</label>
          <Input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="operator@company.com" />
        </div>
        <div className="space-y-2">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <label className="text-sm font-medium text-slate-700">Password</label>
            <span className="text-sm text-slate-400">Password recovery is not available in-app yet.</span>
          </div>
          <PasswordInput value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" />
        </div>
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <Button type="submit" className="w-full py-3 text-base" disabled={submitting}>
          {submitting ? "Signing In..." : "Sign In"}
        </Button>
      </form>
      <p className="mt-8 text-center text-sm text-slate-600">
        Don&apos;t have an account?{" "}
        <Link className="font-medium text-accent-600" to="/signup">
          Create account
        </Link>
      </p>
    </AuthFormShell>
  );
}

export function SignupPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = React.useState({ full_name: "", email: "", password: "", confirm: "" });
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const update = (field: keyof typeof form, value: string) => setForm((current) => ({ ...current, [field]: value }));

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await register({ email: form.email, password: form.password, full_name: form.full_name });
      navigate("/app/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create account.");
    } finally {
      setSubmitting(false);
    }
  };

  const signupCards = [
    { icon: Boxes, title: "Catalog Intelligence", body: "Automated SKU mapping, anomaly detection, and unified product data management." },
    { icon: ListChecks, title: "Approval Workflows", body: "Human-in-the-loop validation for operational changes and AI drafts." },
    { icon: ChartColumnBig, title: "Operational Analytics", body: "Visibility into sync health, support velocity, and risk queues." }
  ];

  return (
    <AuthFormShell
      title="Create Account"
      copy="This account provides secure access to the internal operations console. Please use your work credentials."
      asideTitle="CommerceOps AI"
      asideCopy="The operational control plane for high-velocity merchants."
      asideContent={
        <div className="space-y-4">
          {signupCards.map(({ icon: Icon, title, body }) => (
            <Card key={title} className="p-6">
              <div className="flex items-start gap-4">
                <span className="mt-1 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-50 text-accent-700">
                  <Icon className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-2xl font-semibold text-slate-950">{title}</p>
                  <p className="mt-3 text-sm leading-7 text-slate-600">{body}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      }
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">Full Name</label>
          <Input value={form.full_name} onChange={(event) => update("full_name", event.target.value)} placeholder="Jane Doe" />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">Work Email</label>
          <Input value={form.email} onChange={(event) => update("email", event.target.value)} placeholder="jane.doe@company.com" />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">Password</label>
          <PasswordInput value={form.password} onChange={(event) => update("password", event.target.value)} />
          <p className="text-xs text-slate-500">Use a strong password with at least 8 characters.</p>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">Confirm Password</label>
          <PasswordInput value={form.confirm} onChange={(event) => update("confirm", event.target.value)} />
        </div>
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <Button type="submit" className="w-full py-3 text-base" disabled={submitting}>
          {submitting ? "Creating Account..." : "Create Account"}
        </Button>
      </form>
      <p className="mt-8 text-center text-sm text-slate-600">
        Already have an account?{" "}
        <Link className="font-medium text-accent-600" to="/login">
          Sign in
        </Link>
      </p>
    </AuthFormShell>
  );
}
