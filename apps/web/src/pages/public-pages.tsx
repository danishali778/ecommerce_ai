import * as React from "react";
import { ArrowRight, BadgeCheck, BellRing, Boxes, ChartColumnBig, ListChecks, ShieldCheck, Sparkles, Workflow, Wrench } from "lucide-react";
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
    <section id={id} className="app-container px-6 py-20">
      <div className="max-w-3xl">
        {eyebrow ? <div className="eyebrow">{eyebrow}</div> : null}
        <h2 className="mt-5 text-4xl font-semibold tracking-tight text-slate-950">{title}</h2>
        <p className="mt-4 text-base leading-8 text-slate-600">{copy}</p>
      </div>
      <div className="mt-10">{children}</div>
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
    <div>
      <section className="app-container grid min-h-[78vh] items-center gap-12 px-6 py-16 lg:grid-cols-[1.02fr_0.98fr]">
        <div>
          <div className="eyebrow">
            <Sparkles className="h-3.5 w-3.5" />
            AI-assisted operations with human review
          </div>
          <h1 className="mt-8 max-w-3xl text-5xl font-semibold tracking-tight text-slate-950 md:text-6xl">
            AI-Powered Shopify Operations. <span className="text-accent-600">Human-Controlled Execution.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
            CommerceOps AI gives internal commerce teams one operational control plane for sync, approvals, support drafts, fraud review,
            inventory follow-up, and traceable workflow execution.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link to="/signup">
              <Button className="gap-2 px-6 py-3 text-base">
                Get Started
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="#process">
              <Button variant="secondary" className="px-6 py-3 text-base">
                See How It Works
              </Button>
            </a>
          </div>
          <div className="mt-8 flex flex-wrap gap-3 text-sm text-slate-500">
            <span className="inline-flex items-center gap-2 rounded-full border bg-white px-3 py-2 shadow-sm">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              No black-box execution
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border bg-white px-3 py-2 shadow-sm">
              <ListChecks className="h-4 w-4 text-accent-600" />
              Human approvals stay central
            </span>
          </div>
        </div>

        <Card className="overflow-hidden border-accent-100 shadow-soft">
          <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-5 py-4">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-slate-300" />
              <span className="h-3 w-3 rounded-full bg-slate-300" />
              <span className="h-3 w-3 rounded-full bg-slate-300" />
            </div>
            <div className="w-56 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs text-slate-400">Search orders, drafts, alerts…</div>
          </div>
          <div className="grid min-h-[34rem] grid-cols-[15rem_1fr]">
            <div className="border-r border-slate-200 bg-white p-5">
              <div className="space-y-3">
                {navItems.map(({ label, active }) => (
                  <div
                    key={label}
                    className={`rounded-2xl px-4 py-3 text-sm font-medium ${active ? "bg-accent-50 text-accent-700" : "bg-slate-50 text-slate-600"}`}
                  >
                    {label}
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-5 bg-white p-6">
              <div className="grid gap-4 md:grid-cols-4">
                {[
                  ["Sync health", "99.8%"],
                  ["Pending approvals", "15"],
                  ["Support drafts", "12"],
                  ["Low stock alerts", "5"]
                ].map(([label, value]) => (
                  <div key={label} className="rounded-2xl border border-slate-200 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</p>
                    <p className="mt-3 text-2xl font-semibold text-slate-950">{value}</p>
                  </div>
                ))}
              </div>
              <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
                <div className="rounded-3xl border border-accent-100 bg-accent-50/50 p-5">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-950">AI drafts - review required</p>
                      <p className="text-sm text-slate-600">Open cases that still need a person in the loop.</p>
                    </div>
                    <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-600 shadow-sm">3 pending</span>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-600">Recommendation</p>
                    <p className="mt-3 text-base font-medium text-slate-950">Fraud risk detected</p>
                    <p className="mt-2 text-sm leading-7 text-slate-600">
                      High-velocity shipping address change post-checkout. AI suggests holding fulfillment until reviewed.
                    </p>
                    <div className="mt-4 flex gap-3">
                      <div className="h-10 w-28 rounded-xl bg-accent-500" />
                      <div className="h-10 w-28 rounded-xl bg-slate-100" />
                    </div>
                  </div>
                </div>
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                  <p className="text-sm font-semibold text-slate-950">Recent activity</p>
                  <div className="mt-5 space-y-4">
                    {[1, 2, 3].map((item) => (
                      <div key={item} className="flex gap-3">
                        <span className="mt-1 h-2.5 w-2.5 rounded-full bg-accent-500" />
                        <div className="space-y-2">
                          <div className="h-4 w-44 rounded bg-slate-200" />
                          <div className="h-3 w-56 rounded bg-slate-100" />
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
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {featureCards.map(({ icon: Icon, title, body }) => (
            <Card key={title} className="p-6">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-50 text-accent-700">
                <Icon className="h-5 w-5" />
              </span>
              <h3 className="mt-5 text-lg font-semibold text-slate-950">{title}</h3>
              <p className="mt-3 text-sm leading-7 text-slate-600">{body}</p>
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
        <div className="grid gap-5 xl:grid-cols-4">
          {[
            ["1. Connect store", "Link Shopify and bootstrap stores, permissions, and sync access."],
            ["2. Sync context", "Bring products, orders, customers, inventory, and alerts into the workspace."],
            ["3. Generate drafts", "Use AI to prepare product, support, and supplier drafts with grounded context."],
            ["4. Review safely", "Route changes through approvals, runtime logs, and human-controlled decisions."]
          ].map(([title, body]) => (
            <Card key={title} className="p-6">
              <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
              <p className="mt-3 text-sm leading-7 text-slate-600">{body}</p>
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
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Card className="p-6">
            <div className="flex items-center gap-3">
              <BadgeCheck className="h-5 w-5 text-emerald-600" />
              <p className="text-lg font-semibold text-slate-950">Human-controlled execution</p>
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-600">
              No uncontrolled auto-approval, no silent customer send, and no direct fraud-triggered mutations to Shopify.
            </p>
          </Card>
          <Card className="p-6">
            <div className="flex items-center gap-3">
              <BellRing className="h-5 w-5 text-accent-600" />
              <p className="text-lg font-semibold text-slate-950">Traceability by default</p>
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-600">
              Workflow runs, agent runs, notifications, and audit history make it easy to explain what happened and why.
            </p>
          </Card>
        </div>
      </MarketingSection>

      <section className="app-container px-6 py-20">
        <Card className="overflow-hidden bg-slate-950 p-10 text-white shadow-soft">
          <div className="grid gap-8 xl:grid-cols-[1fr_auto] xl:items-center">
            <div>
              <p className="eyebrow border-white/10 bg-white/5 text-white/70">Ready to work from one operational console?</p>
              <h2 className="mt-5 text-4xl font-semibold tracking-tight">Bring your storefront operations under one reviewable system.</h2>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-white/75">
                Start with auth, stores, sync, and the operator workspaces already defined in the platform design.
              </p>
            </div>
            <div className="flex flex-wrap gap-4">
              <Link to="/signup">
                <Button className="gap-2 bg-white text-slate-950 hover:bg-slate-100">
                  Create account
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <a href="#features">
                <Button variant="ghost" className="border border-white/15 bg-white/5 text-white hover:bg-white/10">
                  Explore features
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
    <div className="app-container grid min-h-[calc(100vh-80px)] gap-0 px-6 py-12 lg:grid-cols-[1fr_1fr]">
      <div className="rounded-l-[2rem] bg-[#eef3ff] p-10">
        <h2 className="text-4xl font-semibold tracking-tight text-slate-950">{asideTitle}</h2>
        <p className="mt-5 max-w-xl text-base leading-8 text-slate-600">{asideCopy}</p>
        <div className="mt-12">{asideContent}</div>
      </div>
      <div className="rounded-r-[2rem] border border-slate-200 bg-white p-10 lg:p-16">
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
          <div className="flex items-center justify-between">
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
