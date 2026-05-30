import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Clipboard, MailCheck, MessagesSquare, RefreshCcw, Search, ShieldCheck, Sparkles, Ticket } from "lucide-react";

import { catalogApi, supportApi } from "@frontend/api-client";
import { Button, Card, Input, Select, Textarea } from "@frontend/ui";
import {
  DetailPanel,
  DraftStatusBanner,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
  MetricCard,
  PageHeader,
  PolicyCitationCard,
  ReviewRequiredBanner,
  SectionCard,
  StatusPill
} from "@/components/common";
import {
  useAddSupportMessage,
  useCreateSupportConversation,
  useGenerateSupportDraft,
  useSupportConversation,
  useSupportConversations,
  useSupportCustomer,
  useSupportCustomers,
  useSupportMessages,
  useSupportOrder,
  useSupportOrders,
  useUpdateSupportConversation
} from "@/hooks/use-support";
import { useCreatePolicy, usePolicies, useUpdatePolicy } from "@/hooks/use-policies";
import { formatDate, titleize } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function customerLabel(customer?: Awaited<ReturnType<typeof catalogApi.getCustomer>>) {
  if (!customer) return "Unlinked customer";
  const fullName = `${customer.first_name ?? ""} ${customer.last_name ?? ""}`.trim();
  return fullName || customer.email || "Customer record";
}

function formatCurrencyAmount(value?: number | string | null, currency?: string | null) {
  if (value === null || value === undefined || value === "") return null;

  const numericValue = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(numericValue)) return null;

  if (currency) {
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency,
        maximumFractionDigits: 2
      }).format(numericValue);
    } catch {
      return `${numericValue.toFixed(2)} ${currency}`;
    }
  }

  return numericValue.toFixed(2);
}

function orderLabel(order?: Awaited<ReturnType<typeof catalogApi.getOrder>>) {
  if (!order) return "Unlinked order";
  const amount = formatCurrencyAmount(order.total, order.currency);
  const reference = order.external_order_id ?? "";

  if (reference.startsWith("gid://shopify/Order/") || /^\d+$/.test(reference)) {
    return amount ? `Linked Shopify order · ${amount}` : "Linked Shopify order";
  }

  if (reference) {
    return amount ? `${reference} · ${amount}` : reference;
  }

  return amount ? `Linked order · ${amount}` : "Linked order";
}

function conversationLabel(conversation: Awaited<ReturnType<typeof supportApi.listConversations>>[number] | Awaited<ReturnType<typeof supportApi.getConversation>>) {
  if (conversation.external_ticket_id) {
    const normalized = conversation.external_ticket_id
      .replace(/^ticket[-_]?/i, "")
      .replace(/[-_]+/g, " ")
      .trim();

    if (!normalized) return "Support ticket";

    const titled = titleize(normalized);
    if (titled.toLowerCase().startsWith("support ")) {
      return `Support Ticket ${titled.slice("support ".length)}`.trim();
    }

    return `Ticket ${titled}`;
  }

  return `${titleize(conversation.channel)} conversation`;
}

function assignedLabel(assignedUserId?: string | null) {
  return assignedUserId ? "Assigned teammate" : "Unassigned";
}

function countByStatus(conversations: Awaited<ReturnType<typeof supportApi.listConversations>>) {
  return {
    open: conversations.filter((conversation) => conversation.status === "open").length,
    pendingReview: conversations.filter((conversation) => conversation.status === "pending_review").length,
    resolved: conversations.filter((conversation) => conversation.status === "resolved").length
  };
}

function DraftActionBanner({
  disposition
}: {
  disposition: "idle" | "approved" | "manual_ready";
}) {
  if (disposition === "approved") {
    return (
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
        Draft approved in this workspace. The operator can continue preparing it for manual send.
      </div>
    );
  }

  if (disposition === "manual_ready") {
    return (
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
        Draft marked ready for manual send. Final delivery still happens in your external support channel.
      </div>
    );
  }

  return null;
}

function SupportMetaList({ items }: { items: Array<{ label: string; value: React.ReactNode }> }) {
  return (
    <div className="overflow-hidden rounded-[1.3rem] border border-slate-200 bg-slate-50/80">
      {items.map((item, index) => (
        <div
          key={item.label}
          className={`flex items-start justify-between gap-4 px-4 py-3 ${index ? "border-t border-slate-200" : ""}`}
        >
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{item.label}</p>
          <div className="max-w-[16rem] text-right text-sm text-slate-800">{item.value}</div>
        </div>
      ))}
    </div>
  );
}

export function SupportPage() {
  const { storeId = "" } = useParams();
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [form, setForm] = useState({
    customer_id: "",
    order_id: "",
    external_ticket_id: "",
    channel: "internal_console"
  });

  const conversationsQuery = useSupportConversations(storeId, statusFilter || undefined);
  const customersQuery = useSupportCustomers(storeId);
  const ordersQuery = useSupportOrders(storeId);
  const createConversation = useCreateSupportConversation(storeId, (conversation) => {
    navigate(`/app/support/${storeId}/conversations/${conversation.id}`);
    setForm({
      customer_id: "",
      order_id: "",
      external_ticket_id: "",
      channel: "internal_console"
    });
  });

  const conversations = conversationsQuery.data ?? [];
  const metrics = countByStatus(conversations);
  const customersById = useMemo(() => new Map((customersQuery.data ?? []).map((customer) => [customer.id, customer])), [customersQuery.data]);
  const ordersById = useMemo(() => new Map((ordersQuery.data ?? []).map((order) => [order.id, order])), [ordersQuery.data]);
  const filteredConversations = conversations.filter((conversation) => {
    if (!search) return true;
    const haystack = [
      conversation.external_ticket_id ?? "",
      conversation.id,
      conversation.channel,
      conversation.customer_id ?? "",
      conversation.order_id ?? "",
      conversation.status
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(search.toLowerCase());
  });

  return (
    <div className="space-y-8">
      <PageHeader
        title="Support workspace"
        description="Review grounded support drafts, preserve manual-send control, and keep customer communication tied to order and policy context."
        actions={
          <Link to={`/app/support/${storeId}/policies`}>
            <Button variant="secondary">Manage Policies</Button>
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Open Conversations" value={metrics.open} hint="Actively being worked by the team" tone={metrics.open ? "warning" : "success"} />
        <MetricCard label="Pending Review" value={metrics.pendingReview} hint="Drafts and cases awaiting human review" tone={metrics.pendingReview ? "info" : "neutral"} />
        <MetricCard label="Resolved" value={metrics.resolved} hint="Closed conversations in the current result set" tone="success" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.18fr)_minmax(21rem,0.82fr)]">
        <SectionCard
          title="Conversation queue"
          actions={
            <div className="flex flex-wrap gap-3">
              <div className="relative min-w-56">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search tickets, customers, or orders" />
              </div>
              <Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="w-44">
                <option value="">All statuses</option>
                <option value="open">Open</option>
                <option value="pending_review">Pending review</option>
                <option value="resolved">Resolved</option>
              </Select>
            </div>
          }
        >
          {conversationsQuery.isLoading ? (
            <LoadingSkeleton rows={5} />
          ) : conversationsQuery.isError ? (
            <ErrorState title="Could not load conversations" message={messageFromError(conversationsQuery.error)} />
          ) : filteredConversations.length === 0 ? (
            <EmptyState
              title="No conversations found"
              message="Create a support conversation for a synced customer and order to start the review flow."
            />
          ) : (
            <div className="space-y-4">
              <div className="rounded-[1.4rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(248,250,252,0.98),rgba(239,246,255,0.82))] px-5 py-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                  <div className="max-w-2xl">
                    <p className="text-sm font-semibold text-slate-950">Review-first support operations</p>
                    <p className="mt-1 text-sm leading-6 text-slate-600">
                      Keep every case grounded in customer, order, and policy context before a human approves the reply and sends it from the external support channel.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-5 text-sm">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">In queue</p>
                      <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">{filteredConversations.length}</p>
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Pending review</p>
                      <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">{metrics.pendingReview}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                {filteredConversations.map((conversation) => (
                  <Link
                    key={conversation.id}
                    to={`/app/support/${storeId}/conversations/${conversation.id}`}
                    className="block rounded-[1.4rem] border border-slate-200 bg-white px-5 py-4 transition hover:-translate-y-[1px] hover:border-accent-300 hover:bg-slate-50"
                  >
                    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_0.82fr_auto]">
                      <div className="min-w-0 space-y-4">
                        <div className="flex items-start gap-3">
                          <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-accent-700">
                            <Ticket className="h-4 w-4" />
                          </span>
                          <div className="min-w-0 space-y-1">
                            <p className="truncate text-base font-semibold text-slate-950">
                              {customerLabel(conversation.customer_id ? customersById.get(conversation.customer_id) : undefined)}
                            </p>
                            <p className="text-sm text-slate-600">{conversationLabel(conversation)}</p>
                          </div>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <StatusPill value={conversation.status} />
                          <StatusPill value={assignedLabel(conversation.assigned_user_id)} />
                          <StatusPill value={titleize(conversation.channel)} />
                        </div>
                      </div>

                      <div className="grid gap-3 text-sm text-slate-600 sm:grid-cols-2 xl:grid-cols-1">
                        <div>
                          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Order</p>
                          <p className="mt-1 leading-6">{orderLabel(conversation.order_id ? ordersById.get(conversation.order_id) : undefined)}</p>
                        </div>
                        <div>
                          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Case</p>
                          <p className="mt-1 leading-6">{conversationLabel(conversation)}</p>
                        </div>
                      </div>

                      <div className="flex flex-col items-start gap-2 text-sm xl:items-end xl:text-right">
                        <div>
                          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Last updated</p>
                          <p className="mt-1 text-slate-700">{formatDate(conversation.updated_at)}</p>
                        </div>
                        <div className="inline-flex items-center gap-2 text-sm font-medium text-accent-600">
                          Open workspace
                          <span aria-hidden="true">→</span>
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </SectionCard>

        <div className="space-y-6 xl:sticky xl:top-24 xl:self-start">
          <SectionCard title="Quick intake">
            <div className="space-y-5">
              <div className="rounded-[1.35rem] border border-slate-200 bg-slate-50/80 px-4 py-4">
                <p className="text-sm font-semibold text-slate-950">Open a new case only when the queue does not already cover it.</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  CommerceOps keeps support review-first: intake, grounded draft generation, operator approval, and manual send outside the platform.
                </p>
              </div>

              <label className="space-y-2 text-sm font-medium text-slate-700">
                Customer
                <Select
                  value={form.customer_id}
                  onChange={(event) => setForm((current) => ({ ...current, customer_id: event.target.value }))}
                >
                  <option value="">Select a customer</option>
                  {(customersQuery.data ?? []).map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.first_name || customer.last_name
                        ? `${customer.first_name ?? ""} ${customer.last_name ?? ""}`.trim()
                        : customer.email ?? "Customer record"}
                    </option>
                  ))}
                </Select>
              </label>

              <label className="space-y-2 text-sm font-medium text-slate-700">
                Order
                <Select value={form.order_id} onChange={(event) => setForm((current) => ({ ...current, order_id: event.target.value }))}>
                  <option value="">Select an order</option>
                  {(ordersQuery.data ?? []).map((order) => (
                    <option key={order.id} value={order.id}>
                      {orderLabel(order)}
                    </option>
                  ))}
                </Select>
              </label>

              <label className="space-y-2 text-sm font-medium text-slate-700">
                External ticket ID
                <Input
                  value={form.external_ticket_id}
                  onChange={(event) => setForm((current) => ({ ...current, external_ticket_id: event.target.value }))}
                  placeholder="ticket-support-001"
                />
              </label>

              <label className="space-y-2 text-sm font-medium text-slate-700">
                Channel
                <Select value={form.channel} onChange={(event) => setForm((current) => ({ ...current, channel: event.target.value }))}>
                  <option value="internal_console">Internal console</option>
                  <option value="email">Email</option>
                  <option value="chat">Chat</option>
                </Select>
              </label>

              <Button
                disabled={createConversation.isPending}
                type="button"
                className="w-full"
                onClick={() =>
                  createConversation.mutate({
                    customer_id: form.customer_id || undefined,
                    order_id: form.order_id || undefined,
                    external_ticket_id: form.external_ticket_id || undefined,
                    channel: form.channel
                  })
                }
              >
                {createConversation.isPending ? "Creating..." : "Create conversation"}
              </Button>

              {createConversation.isError ? (
                <p className="text-sm text-rose-700">{messageFromError(createConversation.error)}</p>
              ) : null}
            </div>
          </SectionCard>

          <div className="surface-panel p-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Operator guardrails</p>
            <div className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                Ground every reply to the linked customer, order, and active store policies.
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                Keep AI output draft-only until a human operator reviews the workspace.
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                Final delivery still happens in the external support tool after approval.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function SupportConversationPage() {
  const { storeId = "", conversationId = "" } = useParams();
  const [queueFilter, setQueueFilter] = useState("");
  const [newMessage, setNewMessage] = useState("");
  const [statusDraft, setStatusDraft] = useState("");
  const [draftDisposition, setDraftDisposition] = useState<"idle" | "approved" | "manual_ready">("idle");

  const queueQuery = useSupportConversations(storeId, queueFilter || undefined);
  const conversationQuery = useSupportConversation(storeId, conversationId);
  const messagesQuery = useSupportMessages(storeId, conversationId);

  const conversation = conversationQuery.data;

  const customerQuery = useSupportCustomer(storeId, conversation?.customer_id);
  const orderQuery = useSupportOrder(storeId, conversation?.order_id);
  const addMessage = useAddSupportMessage(storeId, conversationId, () => {
    setNewMessage("");
  });
  const updateConversation = useUpdateSupportConversation(storeId, conversationId);
  const generateDraft = useGenerateSupportDraft(storeId, conversationId);

  const queue = queueQuery.data ?? [];
  const messages = messagesQuery.data ?? [];
  const latestAiDraft = useMemo(
    () => [...messages].reverse().find((message) => message.generated_by_ai && message.direction === "draft_outbound"),
    [messages]
  );

  useEffect(() => {
    setDraftDisposition("idle");
  }, [latestAiDraft?.id]);

  if (conversationQuery.isLoading) return <LoadingSkeleton rows={6} />;
  if (conversationQuery.isError || !conversation) {
    return <ErrorState title="Could not load conversation" message={messageFromError(conversationQuery.error)} />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title={conversationLabel(conversation)}
        description="Review message history, generate grounded drafts, and keep final delivery under operator control."
        actions={
          <div className="flex flex-wrap gap-3">
            <Select value={statusDraft || conversation.status} onChange={(event) => setStatusDraft(event.target.value)} className="w-48">
              <option value="open">Open</option>
              <option value="pending_review">Pending review</option>
              <option value="resolved">Resolved</option>
            </Select>
            <Button
              variant="secondary"
              onClick={() => updateConversation.mutate(statusDraft || conversation.status)}
              disabled={updateConversation.isPending}
            >
              Save status
            </Button>
            <Button onClick={() => generateDraft.mutate()} disabled={generateDraft.isPending}>
              {generateDraft.isPending ? "Generating..." : "Generate reply draft"}
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[18rem_minmax(0,1fr)_21rem]">
        <SectionCard
          title="Conversation queue"
          actions={
            <Select value={queueFilter} onChange={(event) => setQueueFilter(event.target.value)} className="w-44">
              <option value="">All statuses</option>
              <option value="open">Open</option>
              <option value="pending_review">Pending review</option>
              <option value="resolved">Resolved</option>
            </Select>
          }
        >
          {queueQuery.isLoading ? (
            <LoadingSkeleton rows={5} />
          ) : queueQuery.isError ? (
            <ErrorState title="Could not load queue" message={messageFromError(queueQuery.error)} />
          ) : (
            <div className="space-y-3">
              {queue.map((entry) => (
                <Link
                  key={entry.id}
                  to={`/app/support/${storeId}/conversations/${entry.id}`}
                  className={`block rounded-xl border px-4 py-4 transition ${
                    entry.id === conversationId ? "border-accent-300 bg-accent-50" : "border-slate-200 bg-white hover:border-accent-200 hover:bg-slate-50"
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <p className="font-semibold text-slate-950">{conversationLabel(entry)}</p>
                        <p className="text-xs text-slate-500">{assignedLabel(entry.assigned_user_id)}</p>
                      </div>
                      <p className="text-[11px] text-slate-500">{formatDate(entry.updated_at)}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <StatusPill value={entry.status} />
                      <StatusPill value={titleize(entry.channel)} />
                      {entry.id === conversationId ? <StatusPill value="selected" /> : null}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </SectionCard>

        <div className="space-y-6">
          <div className="surface-panel overflow-hidden">
            <div className="border-b border-slate-200 px-5 py-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-accent-700">
                      <MessagesSquare className="h-4 w-4" />
                    </span>
                    <div className="space-y-1">
                      <p className="text-lg font-semibold text-slate-950">{customerLabel(customerQuery.data)}</p>
                      <p className="text-sm text-slate-600">{conversationLabel(conversation)}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <StatusPill value={conversation.status} />
                    <StatusPill value={titleize(conversation.channel)} />
                    {latestAiDraft ? <StatusPill value={latestAiDraft.status} /> : null}
                  </div>
                </div>
                <div className="space-y-1 text-sm text-slate-500 sm:text-right">
                  <p>Created {formatDate(conversation.created_at)}</p>
                  <p>Updated {formatDate(conversation.updated_at)}</p>
                </div>
              </div>
            </div>

            <div className="grid gap-4 px-5 py-5 md:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Linked order</p>
                <p className="mt-2 text-sm leading-6 text-slate-700">{orderLabel(orderQuery.data)}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Assignment</p>
                <p className="mt-2 text-sm leading-6 text-slate-700">{assignedLabel(conversation.assigned_user_id)}</p>
              </div>
            </div>
          </div>

          <SectionCard title="Conversation thread">
            {messagesQuery.isLoading ? (
              <LoadingSkeleton rows={4} />
            ) : messagesQuery.isError ? (
              <ErrorState title="Could not load messages" message={messageFromError(messagesQuery.error)} />
            ) : (
              <div className="space-y-4">
                {messages.map((message) => {
                  const isAiDraft = message.generated_by_ai;
                  const messageLabel =
                    message.direction === "inbound"
                      ? "Customer message"
                      : isAiDraft
                        ? "Internal AI draft"
                        : titleize(message.direction);

                  return (
                    <div
                      key={message.id}
                      className={`rounded-[1.35rem] border p-4 ${
                        isAiDraft
                          ? "border-blue-200 bg-[linear-gradient(135deg,rgba(239,246,255,0.96),rgba(255,255,255,0.98))]"
                          : "border-slate-200 bg-white"
                      }`}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold text-slate-950">{messageLabel}</p>
                          <StatusPill value={message.status} />
                          {isAiDraft ? <StatusPill value="generated_by_ai" /> : null}
                        </div>
                        <p className="text-xs text-slate-500">{formatDate(message.created_at)}</p>
                      </div>

                      <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">{message.body}</p>

                      <div className="mt-4 flex flex-wrap gap-4 text-xs text-slate-500">
                        {message.confidence_score !== null && message.confidence_score !== undefined ? (
                          <span>Confidence {(message.confidence_score * 100).toFixed(0)}%</span>
                        ) : null}
                        {message.cited_order_facts_summary ? <span>Grounded to current order context</span> : null}
                      </div>

                      {message.cited_order_facts_summary ? (
                        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
                          {message.cited_order_facts_summary}
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            )}
          </SectionCard>

          {latestAiDraft ? (
            <SectionCard title="Reply workshop">
              <div className="space-y-4">
                <div className="flex flex-wrap items-start justify-between gap-3 rounded-[1.35rem] border border-blue-200 bg-[linear-gradient(135deg,rgba(239,246,255,0.96),rgba(255,255,255,0.98))] p-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-white text-accent-700 shadow-sm">
                        <Sparkles className="h-4 w-4" />
                      </span>
                      <div>
                        <p className="font-semibold text-slate-950">CommerceOps AI (Internal Draft)</p>
                        <p className="text-sm text-slate-600">Generated {formatDate(latestAiDraft.created_at)}</p>
                      </div>
                    </div>
                    <DraftStatusBanner status={latestAiDraft.status} modelName="Support agent" />
                  </div>
                  <StatusPill value={latestAiDraft.needs_human_review ? "operator_review_required" : "reviewed"} />
                </div>

                {latestAiDraft.needs_human_review ? (
                  <ReviewRequiredBanner
                    message={`Operator Review Required${latestAiDraft.review_reason_code ? ` - ${titleize(latestAiDraft.review_reason_code)}` : ""}.`}
                  />
                ) : null}

                <Card className="border-slate-200 bg-slate-50 p-5">
                  <p className="whitespace-pre-wrap text-sm leading-7 text-slate-700">{latestAiDraft.body}</p>
                </Card>

                <div className="flex flex-wrap gap-3">
                  <Button onClick={() => setDraftDisposition("approved")}>
                    <ShieldCheck className="mr-2 h-4 w-4" />
                    Approve Draft
                  </Button>
                  <Button variant="secondary" onClick={() => setDraftDisposition("manual_ready")}>
                    <MailCheck className="mr-2 h-4 w-4" />
                    Mark Ready for Manual Send
                  </Button>
                  <Button variant="secondary" onClick={() => navigator.clipboard?.writeText(latestAiDraft.body)}>
                    <Clipboard className="mr-2 h-4 w-4" />
                    Copy Draft
                  </Button>
                  <Button variant="ghost" onClick={() => generateDraft.mutate()} disabled={generateDraft.isPending}>
                    <RefreshCcw className="mr-2 h-4 w-4" />
                    Regenerate
                  </Button>
                </div>

                <DraftActionBanner disposition={draftDisposition} />
              </div>
            </SectionCard>
          ) : (
            <EmptyState
              title="No internal draft yet"
              message="Generate a grounded reply draft once enough order and policy context is available."
              action={
                <Button onClick={() => generateDraft.mutate()} disabled={generateDraft.isPending}>
                  {generateDraft.isPending ? "Generating..." : "Generate draft"}
                </Button>
              }
            />
          )}

          <SectionCard title="Log inbound message">
            <div className="space-y-4">
              <Textarea
                value={newMessage}
                onChange={(event) => setNewMessage(event.target.value)}
                rows={6}
                placeholder="Paste the latest customer message here..."
              />
              <div className="flex justify-end">
                <Button
                  disabled={addMessage.isPending || !newMessage.trim()}
                  onClick={() => addMessage.mutate({ direction: "inbound", body: newMessage })}
                >
                  {addMessage.isPending ? "Logging..." : "Add inbound message"}
                </Button>
              </div>
            </div>
          </SectionCard>
        </div>

        <div className="space-y-6 xl:sticky xl:top-24 xl:self-start">
          <DetailPanel title="Conversation context" subtitle="Customer, order, and case metadata used to ground the workspace">
            <SupportMetaList
              items={[
                { label: "Status", value: <StatusPill value={conversation.status} /> },
                { label: "Channel", value: titleize(conversation.channel) },
                { label: "Customer", value: customerLabel(customerQuery.data) },
                { label: "Order", value: orderLabel(orderQuery.data) },
                { label: "Assignment", value: assignedLabel(conversation.assigned_user_id) },
                { label: "Ticket", value: conversationLabel(conversation) }
              ]}
            />
          </DetailPanel>

          {latestAiDraft ? (
            <SectionCard title="AI insights">
              <div className="space-y-4">
                <Card className="border-emerald-200 bg-emerald-50 p-4">
                  <p className="text-sm font-semibold text-emerald-900">Draft confidence</p>
                  <p className="mt-2 text-2xl font-semibold text-slate-950">
                    {latestAiDraft.confidence_score !== null && latestAiDraft.confidence_score !== undefined
                      ? `${(latestAiDraft.confidence_score * 100).toFixed(0)}%`
                      : "Pending"}
                  </p>
                  <p className="mt-2 text-sm text-emerald-800">
                    Confidence reflects the available order facts and policy matches, not autonomous send authority.
                  </p>
                </Card>

                {latestAiDraft.cited_policy_chunks_json.length > 0 ? (
                  <div className="space-y-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Cited context</p>
                    {latestAiDraft.cited_policy_chunks_json.map((chunk, index) => (
                      <PolicyCitationCard
                        key={`${latestAiDraft.id}-${index}`}
                        title={String(chunk.chunk_id ?? `Policy chunk ${index + 1}`)}
                        body={String(chunk.rationale ?? "Policy-grounded support context")}
                      />
                    ))}
                  </div>
                ) : null}
              </div>
            </SectionCard>
          ) : null}

          <SectionCard title="Internal review state">
            <div className="space-y-4 text-sm text-slate-600">
              <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4">
                <p className="font-medium text-slate-900">Operator review posture</p>
                <p className="mt-2">
                  CommerceOps prepares drafts in-platform. Final customer delivery still happens in your external support system after human review.
                </p>
              </div>
              {latestAiDraft?.cited_order_facts_summary ? (
                <Card className="p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Order grounding</p>
                  <p className="mt-2 leading-7 text-slate-700">{latestAiDraft.cited_order_facts_summary}</p>
                </Card>
              ) : null}
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}

export function PoliciesPage() {
  const { storeId = "" } = useParams();
  const [selectedPolicyId, setSelectedPolicyId] = useState("");
  const [search, setSearch] = useState("");
  const [draft, setDraft] = useState({
    document_type: "returns",
    source_type: "manual",
    title: "",
    content: "",
    version: "v1"
  });

  const policiesQuery = usePolicies(storeId);

  const selectedPolicy = useMemo(
    () => (policiesQuery.data ?? []).find((policy) => policy.id === selectedPolicyId) ?? null,
    [policiesQuery.data, selectedPolicyId]
  );

  const filteredPolicies = useMemo(() => {
    const policies = policiesQuery.data ?? [];
    if (!search) return policies;
    return policies.filter((policy) =>
      [policy.title, policy.document_type, policy.source_type, policy.version ?? "", policy.embedding_status]
        .join(" ")
        .toLowerCase()
        .includes(search.toLowerCase())
    );
  }, [policiesQuery.data, search]);

  const createPolicy = useCreatePolicy(storeId, () => {
    setDraft({ document_type: "returns", source_type: "manual", title: "", content: "", version: "v1" });
  });
  const updatePolicy = useUpdatePolicy(storeId, selectedPolicy?.id ?? null);

  const policies = policiesQuery.data ?? [];
  const indexedPolicies = policies.filter((policy) => policy.embedding_status === "ready").length;
  const activePolicies = policies.filter((policy) => policy.is_active).length;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Policy documents"
        description="Maintain the knowledge base that grounds support drafts with reviewable, versioned store policy content."
        actions={
          <Link to={`/app/support/${storeId}/conversations`}>
            <Button variant="secondary">Back to support</Button>
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Active Policies" value={activePolicies} hint="Policies currently contributing to grounded support" tone={activePolicies ? "success" : "neutral"} />
        <MetricCard label="Indexed" value={indexedPolicies} hint="Embedding pipeline completed successfully" tone={indexedPolicies ? "info" : "warning"} />
        <MetricCard label="Library Size" value={policies.length} hint="Documents available in the current store policy library" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.15fr]">
        <SectionCard
          title="Policy library"
          actions={
            <div className="relative min-w-56">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search policy titles or types" />
            </div>
          }
        >
          {policiesQuery.isLoading ? (
            <LoadingSkeleton rows={4} />
          ) : policiesQuery.isError ? (
            <ErrorState title="Could not load policies" message={messageFromError(policiesQuery.error)} />
          ) : filteredPolicies.length === 0 ? (
            <EmptyState title="No policies yet" message="Create your first policy to support grounded AI draft generation." />
          ) : (
            <div className="space-y-3">
              {filteredPolicies.map((policy) => (
                <button
                  key={policy.id}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    selectedPolicyId === policy.id ? "border-accent-300 bg-accent-50" : "border-slate-200 bg-white hover:border-accent-200"
                  }`}
                  onClick={() => {
                    setSelectedPolicyId(policy.id);
                    setDraft({
                      document_type: policy.document_type,
                      source_type: policy.source_type,
                      title: policy.title,
                      content: policy.content,
                      version: policy.version ?? "v1"
                    });
                  }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-2">
                      <p className="font-semibold text-slate-950">{policy.title}</p>
                      <div className="flex flex-wrap gap-2">
                        <StatusPill value={policy.document_type} />
                        <StatusPill value={policy.embedding_status} />
                      </div>
                      <p className="text-sm text-slate-600">
                        Version {policy.version ?? "v1"} - Source {titleize(policy.source_type)}
                      </p>
                    </div>
                    <p className="text-xs text-slate-500">{formatDate(policy.updated_at)}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </SectionCard>

        <div className="space-y-6">
          {selectedPolicy ? (
            <DetailPanel title="Selected policy" subtitle="Document metadata currently grounding support generation">
              <KeyValueGrid
                items={[
                  { label: "Title", value: selectedPolicy.title },
                  { label: "Document type", value: titleize(selectedPolicy.document_type) },
                  { label: "Source type", value: titleize(selectedPolicy.source_type) },
                  { label: "Version", value: selectedPolicy.version ?? "v1" },
                  { label: "Embedding", value: <StatusPill value={selectedPolicy.embedding_status} /> },
                  { label: "Updated", value: formatDate(selectedPolicy.updated_at) }
                ]}
              />
            </DetailPanel>
          ) : (
            <DetailPanel title="New policy" subtitle="Use the editor below to add a new policy document to the library." />
          )}

          <SectionCard title={selectedPolicy ? "Edit policy" : "Create policy"}>
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <label className="space-y-2 text-sm font-medium text-slate-700">
                  Document type
                  <Select value={draft.document_type} onChange={(event) => setDraft((current) => ({ ...current, document_type: event.target.value }))}>
                    <option value="returns">Returns</option>
                    <option value="shipping">Shipping</option>
                    <option value="refunds">Refunds</option>
                    <option value="support">Support</option>
                  </Select>
                </label>
                <label className="space-y-2 text-sm font-medium text-slate-700">
                  Version
                  <Input value={draft.version} onChange={(event) => setDraft((current) => ({ ...current, version: event.target.value }))} />
                </label>
              </div>

              <label className="space-y-2 text-sm font-medium text-slate-700">
                Title
                <Input value={draft.title} onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} />
              </label>

              <label className="space-y-2 text-sm font-medium text-slate-700">
                Content
                <Textarea
                  rows={14}
                  value={draft.content}
                  onChange={(event) => setDraft((current) => ({ ...current, content: event.target.value }))}
                  placeholder="Paste the policy content that should ground AI support replies..."
                />
              </label>

              <div className="flex flex-wrap gap-3">
                {selectedPolicy ? (
                  <Button
                    onClick={() =>
                      updatePolicy.mutate({
                        title: draft.title,
                        content: draft.content,
                        version: draft.version
                      })
                    }
                    disabled={updatePolicy.isPending}
                  >
                    {updatePolicy.isPending ? "Saving..." : "Save policy"}
                  </Button>
                ) : (
                  <Button onClick={() => createPolicy.mutate(draft)} disabled={createPolicy.isPending}>
                    {createPolicy.isPending ? "Creating..." : "Create policy"}
                  </Button>
                )}
                {selectedPolicy ? (
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setSelectedPolicyId("");
                      setDraft({ document_type: "returns", source_type: "manual", title: "", content: "", version: "v1" });
                    }}
                  >
                    New policy
                  </Button>
                ) : null}
              </div>

              {(createPolicy.isError || updatePolicy.isError) ? (
                <p className="text-sm text-rose-700">{messageFromError(createPolicy.error ?? updatePolicy.error)}</p>
              ) : null}
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
