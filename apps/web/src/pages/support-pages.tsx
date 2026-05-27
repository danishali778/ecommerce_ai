import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { catalogApi, policiesApi, supportApi } from "@frontend/api-client";
import { Button, Card, Input, Select, Textarea } from "@frontend/ui";
import {
  DetailPanel,
  DraftStatusBanner,
  EmptyState,
  ErrorState,
  KeyValueGrid,
  LoadingSkeleton,
  PageHeader,
  PolicyCitationCard,
  ReviewRequiredBanner,
  SectionCard,
  StatusPill
} from "@/components/common";
import { formatDate } from "@/lib/format";

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

export function SupportPage() {
  const { storeId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [form, setForm] = useState({
    customer_id: "",
    order_id: "",
    external_ticket_id: "",
    channel: "internal_console"
  });

  const conversationsQuery = useQuery({
    queryKey: ["support", "conversations", storeId, statusFilter],
    queryFn: () => supportApi.listConversations(storeId, statusFilter || undefined),
    enabled: Boolean(storeId)
  });

  const customersQuery = useQuery({
    queryKey: ["support", "customers", storeId],
    queryFn: () => catalogApi.listCustomers(storeId),
    enabled: Boolean(storeId)
  });

  const ordersQuery = useQuery({
    queryKey: ["support", "orders", storeId],
    queryFn: () => catalogApi.listOrders(storeId),
    enabled: Boolean(storeId)
  });

  const createConversation = useMutation({
    mutationFn: () =>
      supportApi.createConversation(storeId, {
        customer_id: form.customer_id || undefined,
        order_id: form.order_id || undefined,
        external_ticket_id: form.external_ticket_id || undefined,
        channel: form.channel
      }),
    onSuccess: (conversation) => {
      queryClient.invalidateQueries({ queryKey: ["support", "conversations", storeId] });
      navigate(`/app/support/${storeId}/conversations/${conversation.id}`);
      setForm({
        customer_id: "",
        order_id: "",
        external_ticket_id: "",
        channel: "internal_console"
      });
    }
  });

  const conversations = conversationsQuery.data ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Support workspace"
        description="Track customer cases, ground replies with order and policy context, and generate internal drafts for operator review."
        actions={
          <Link to={`/app/support/${storeId}/policies`}>
            <Button variant="secondary">Manage Policies</Button>
          </Link>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
        <SectionCard
          title="Active conversations"
          actions={
            <Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="w-44">
              <option value="">All statuses</option>
              <option value="open">Open</option>
              <option value="pending_review">Pending review</option>
              <option value="resolved">Resolved</option>
            </Select>
          }
        >
          {conversationsQuery.isLoading ? (
            <LoadingSkeleton rows={5} />
          ) : conversationsQuery.isError ? (
            <ErrorState title="Could not load conversations" message={messageFromError(conversationsQuery.error)} />
          ) : conversations.length === 0 ? (
            <EmptyState
              title="No conversations yet"
              message="Create a support conversation for a synced order and customer to start the review flow."
            />
          ) : (
            <div className="space-y-3">
              {conversations.map((conversation) => (
                <Card key={conversation.id} className="p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-slate-950">{conversation.external_ticket_id ?? conversation.id}</p>
                        <StatusPill value={conversation.status} />
                      </div>
                      <p className="text-sm text-slate-600">
                        Channel: {conversation.channel.replaceAll("_", " ")} · Created {formatDate(conversation.created_at)}
                      </p>
                      <p className="text-xs text-slate-500">
                        Customer {conversation.customer_id ?? "unlinked"} · Order {conversation.order_id ?? "unlinked"}
                      </p>
                    </div>
                    <Link to={`/app/support/${storeId}/conversations/${conversation.id}`}>
                      <Button>Open conversation</Button>
                    </Link>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard title="Create conversation">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              createConversation.mutate();
            }}
          >
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
                      : customer.email ?? customer.id}
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
                    {order.external_order_id} · {order.total} {order.currency ?? ""}
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

            <Button disabled={createConversation.isPending} type="submit" className="w-full">
              {createConversation.isPending ? "Creating..." : "Create conversation"}
            </Button>

            {createConversation.isError ? (
              <p className="text-sm text-rose-700">{messageFromError(createConversation.error)}</p>
            ) : null}
          </form>
        </SectionCard>
      </div>
    </div>
  );
}

export function SupportConversationPage() {
  const { storeId = "", conversationId = "" } = useParams();
  const queryClient = useQueryClient();
  const [newMessage, setNewMessage] = useState("");
  const [statusDraft, setStatusDraft] = useState("");
  const [draftReady, setDraftReady] = useState(false);

  const conversationQuery = useQuery({
    queryKey: ["support", "conversation", storeId, conversationId],
    queryFn: () => supportApi.getConversation(storeId, conversationId),
    enabled: Boolean(storeId && conversationId)
  });

  const messagesQuery = useQuery({
    queryKey: ["support", "messages", storeId, conversationId],
    queryFn: () => supportApi.listMessages(storeId, conversationId),
    enabled: Boolean(storeId && conversationId)
  });

  const conversation = conversationQuery.data;

  const customerQuery = useQuery({
    queryKey: ["support", "customer", storeId, conversation?.customer_id],
    queryFn: () => catalogApi.getCustomer(storeId, conversation!.customer_id!),
    enabled: Boolean(storeId && conversation?.customer_id)
  });

  const orderQuery = useQuery({
    queryKey: ["support", "order", storeId, conversation?.order_id],
    queryFn: () => catalogApi.getOrder(storeId, conversation!.order_id!),
    enabled: Boolean(storeId && conversation?.order_id)
  });

  const addMessage = useMutation({
    mutationFn: () => supportApi.createMessage(storeId, conversationId, { direction: "inbound", body: newMessage }),
    onSuccess: () => {
      setNewMessage("");
      queryClient.invalidateQueries({ queryKey: ["support", "messages", storeId, conversationId] });
    }
  });

  const updateConversation = useMutation({
    mutationFn: (nextStatus: string) => supportApi.updateConversation(storeId, conversationId, nextStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["support", "conversation", storeId, conversationId] });
    }
  });

  const generateDraft = useMutation({
    mutationFn: () => supportApi.generateDraft(storeId, conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["support", "messages", storeId, conversationId] });
      setDraftReady(true);
    }
  });

  const messages = messagesQuery.data ?? [];
  const latestAiDraft = useMemo(
    () => [...messages].reverse().find((message) => message.generated_by_ai && message.direction === "draft_outbound"),
    [messages]
  );

  if (conversationQuery.isLoading) return <LoadingSkeleton rows={6} />;
  if (conversationQuery.isError || !conversation) {
    return <ErrorState title="Could not load conversation" message={messageFromError(conversationQuery.error)} />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title={`Support conversation ${conversation.external_ticket_id ?? conversation.id}`}
        description="Ground each reply with order facts and policies, then prepare a reviewable internal draft for manual handling."
        actions={
          <div className="flex flex-wrap gap-3">
            <Select value={statusDraft || conversation.status} onChange={(event) => setStatusDraft(event.target.value)} className="w-48">
              <option value="open">Open</option>
              <option value="pending_review">Pending review</option>
              <option value="resolved">Resolved</option>
            </Select>
            <Button
              variant="secondary"
              onClick={() => {
                const nextStatus = statusDraft || conversation.status;
                setStatusDraft(nextStatus);
                updateConversation.mutate(nextStatus);
              }}
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

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
        <div className="space-y-6">
          <SectionCard title="Conversation thread">
            {messagesQuery.isLoading ? (
              <LoadingSkeleton rows={4} />
            ) : messagesQuery.isError ? (
              <ErrorState title="Could not load messages" message={messageFromError(messagesQuery.error)} />
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <Card
                    key={message.id}
                    className={message.direction === "draft_outbound" ? "border-blue-200 bg-blue-50 p-4" : "p-4"}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-slate-950">
                        {message.direction === "inbound" ? "Customer message" : "Internal AI draft"}
                      </p>
                      <StatusPill value={message.status} />
                      {message.generated_by_ai ? <StatusPill value="generated_by_ai" /> : null}
                    </div>
                    <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">{message.body}</p>
                    <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
                      <span>{formatDate(message.created_at)}</span>
                      {message.confidence_score !== null && message.confidence_score !== undefined ? (
                        <span>Confidence: {(message.confidence_score * 100).toFixed(0)}%</span>
                      ) : null}
                      {message.cited_order_facts_summary ? <span>{message.cited_order_facts_summary}</span> : null}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard title="Log inbound message">
            <div className="space-y-4">
              <Textarea
                value={newMessage}
                onChange={(event) => setNewMessage(event.target.value)}
                rows={6}
                placeholder="Paste the latest customer message here..."
              />
              <div className="flex justify-end">
                <Button disabled={addMessage.isPending || !newMessage.trim()} onClick={() => addMessage.mutate()}>
                  {addMessage.isPending ? "Logging..." : "Add inbound message"}
                </Button>
              </div>
            </div>
          </SectionCard>
        </div>

        <div className="space-y-6">
          <DetailPanel title="Conversation context" subtitle="Order, customer, and workflow grounding used by the support agent">
            <KeyValueGrid
              items={[
                { label: "Status", value: <StatusPill value={conversation.status} /> },
                { label: "Channel", value: conversation.channel.replaceAll("_", " ") },
                {
                  label: "Customer",
                  value: conversation.customer_id
                    ? `${customerQuery.data?.first_name ?? ""} ${customerQuery.data?.last_name ?? ""}`.trim() ||
                      customerQuery.data?.email ||
                      conversation.customer_id
                    : "Unlinked"
                },
                {
                  label: "Order",
                  value: conversation.order_id
                    ? `${orderQuery.data?.external_order_id ?? conversation.order_id} · ${orderQuery.data?.total ?? ""} ${
                        orderQuery.data?.currency ?? ""
                      }`
                    : "Unlinked"
                }
              ]}
            />
          </DetailPanel>

          {latestAiDraft ? (
            <div className="space-y-4">
              <DraftStatusBanner status={latestAiDraft.status} modelName="Support agent" />
              {latestAiDraft.needs_human_review ? (
                <ReviewRequiredBanner
                  message={`Operator review required${latestAiDraft.review_reason_code ? `: ${latestAiDraft.review_reason_code.replaceAll("_", " ")}` : ""}.`}
                />
              ) : null}

              {latestAiDraft.cited_policy_chunks_json.length > 0 ? (
                <SectionCard title="Cited policy context">
                  <div className="space-y-3">
                    {latestAiDraft.cited_policy_chunks_json.map((chunk, index) => (
                      <PolicyCitationCard
                        key={`${latestAiDraft.id}-${index}`}
                        title={String(chunk.chunk_id ?? `Policy chunk ${index + 1}`)}
                        body={String(chunk.rationale ?? "Policy-grounded support context")}
                      />
                    ))}
                  </div>
                </SectionCard>
              ) : null}

              <SectionCard title="Operator next steps">
                <div className="space-y-3 text-sm text-slate-600">
                  <p>
                    Drafts remain internal. CommerceOps prepares the response, but final customer delivery still happens outside the
                    platform.
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <Button variant="secondary" onClick={() => navigator.clipboard.writeText(latestAiDraft.body)}>
                      Copy draft
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => setDraftReady(true)}
                    >
                      Mark ready for manual send
                    </Button>
                  </div>
                  {draftReady ? (
                    <p className="rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-emerald-800">
                      Draft marked ready for manual send in this workspace. The actual send still happens in your support system.
                    </p>
                  ) : null}
                </div>
              </SectionCard>
            </div>
          ) : (
            <EmptyState
              title="No internal draft yet"
              message="Generate a reply draft once enough support context is available."
              action={
                <Button onClick={() => generateDraft.mutate()} disabled={generateDraft.isPending}>
                  {generateDraft.isPending ? "Generating..." : "Generate draft"}
                </Button>
              }
            />
          )}
        </div>
      </div>
    </div>
  );
}

export function PoliciesPage() {
  const { storeId = "" } = useParams();
  const queryClient = useQueryClient();
  const [selectedPolicyId, setSelectedPolicyId] = useState("");
  const [draft, setDraft] = useState({
    document_type: "returns",
    source_type: "manual",
    title: "",
    content: "",
    version: "v1"
  });

  const policiesQuery = useQuery({
    queryKey: ["policies", storeId],
    queryFn: () => policiesApi.list(storeId),
    enabled: Boolean(storeId)
  });

  const selectedPolicy = useMemo(
    () => (policiesQuery.data ?? []).find((policy) => policy.id === selectedPolicyId) ?? null,
    [policiesQuery.data, selectedPolicyId]
  );

  const createPolicy = useMutation({
    mutationFn: () => policiesApi.create(storeId, draft),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["policies", storeId] });
      setDraft({ document_type: "returns", source_type: "manual", title: "", content: "", version: "v1" });
    }
  });

  const updatePolicy = useMutation({
    mutationFn: () =>
      selectedPolicy
        ? policiesApi.update(storeId, selectedPolicy.id, {
            title: draft.title,
            content: draft.content,
            version: draft.version
          })
        : Promise.reject(new Error("No policy selected")),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["policies", storeId] });
    }
  });

  return (
    <div className="space-y-8">
      <PageHeader
        title="Policy documents"
        description="Maintain the policy knowledge base used by the support workspace for grounded reply generation."
        actions={
          <Link to={`/app/support/${storeId}/conversations`}>
            <Button variant="secondary">Back to support</Button>
          </Link>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_1.1fr]">
        <SectionCard title="Policy library">
          {policiesQuery.isLoading ? (
            <LoadingSkeleton rows={4} />
          ) : policiesQuery.isError ? (
            <ErrorState title="Could not load policies" message={messageFromError(policiesQuery.error)} />
          ) : (policiesQuery.data ?? []).length === 0 ? (
            <EmptyState title="No policies yet" message="Create your first policy to support grounded AI draft generation." />
          ) : (
            <div className="space-y-3">
              {(policiesQuery.data ?? []).map((policy) => (
                <button
                  key={policy.id}
                  className={`w-full rounded-2xl border p-4 text-left ${
                    selectedPolicyId === policy.id ? "border-accent-300 bg-accent-50" : "border-slate-200 bg-white"
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
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-950">{policy.title}</p>
                      <p className="mt-1 text-sm text-slate-600">{policy.document_type.replaceAll("_", " ")}</p>
                    </div>
                    <StatusPill value={policy.embedding_status} />
                  </div>
                </button>
              ))}
            </div>
          )}
        </SectionCard>

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
                rows={12}
                value={draft.content}
                onChange={(event) => setDraft((current) => ({ ...current, content: event.target.value }))}
                placeholder="Paste the policy content that should ground AI support replies..."
              />
            </label>

            <div className="flex flex-wrap gap-3">
              {selectedPolicy ? (
                <Button onClick={() => updatePolicy.mutate()} disabled={updatePolicy.isPending}>
                  {updatePolicy.isPending ? "Saving..." : "Save policy"}
                </Button>
              ) : (
                <Button onClick={() => createPolicy.mutate()} disabled={createPolicy.isPending}>
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
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
