import { appConfig } from "@frontend/config";
import type {
  AnalyticsAutomationResponse,
  AnalyticsOverviewResponse,
  ApiEnvelope,
  ApprovalActionResponse,
  ApprovalResponse,
  AuditEventSummary,
  AuthTokenResponse,
  CustomerSummary,
  DashboardSummaryResponse,
  DraftApprovalSubmissionResponse,
  DraftGenerationAcceptedResponse,
  IntegrationSummary,
  InventoryAlertResponse,
  MeResponse,
  NotificationSummary,
  OrderRiskScoreResponse,
  OrderSummary,
  OrganizationCreateRequest,
  OrganizationResponse,
  PolicyDocumentResponse,
  ProductDetail,
  ProductDraftSummary,
  ProductSummary,
  ReorderSuggestionResponse,
  RiskReviewResponse,
  StoreCreateRequest,
  StoreSummary,
  SupportConversationResponse,
  SupportDraftGenerationAcceptedResponse,
  SupportMessageResponse,
  SyncRunSummary,
  UserResponse,
  WorkflowRunSummary,
  AgentRunSummary,
  RoleSummary,
  CreateUserRequest,
  UpdateUserRequest
} from "@frontend/types";

type AuthBridge = {
  getAccessToken?: () => string | null;
  refreshAccessToken?: () => Promise<string | null>;
};

let authBridge: AuthBridge = {};

export function configureApiAuth(bridge: AuthBridge) {
  authBridge = bridge;
}

class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

function withQuery(path: string, query?: Record<string, string | number | boolean | undefined | null>) {
  if (!query) return path;
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    params.set(key, String(value));
  });
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  headers.set("Content-Type", "application/json");
  const accessToken = authBridge.getAccessToken?.();
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  const response = await fetch(`${appConfig.apiBaseUrl}${path}`, {
    credentials: "include",
    ...init,
    headers
  });

  if (response.status === 401 && retry && authBridge.refreshAccessToken) {
    const nextToken = await authBridge.refreshAccessToken();
    if (nextToken) {
      return request<T>(path, init, false);
    }
  }

  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(text || "Request failed", response.status);
  }

  const data = (await response.json()) as ApiEnvelope<T>;
  return data.data;
}

export const authApi = {
  register(payload: { email: string; password: string; full_name: string }) {
    return request<AuthTokenResponse>("/auth/register", { method: "POST", body: JSON.stringify(payload) });
  },
  login(payload: { email: string; password: string }) {
    return request<AuthTokenResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) });
  },
  refresh() {
    return request<AuthTokenResponse>("/auth/refresh", { method: "POST", body: JSON.stringify({}) });
  },
  logout() {
    return request<{ logged_out: boolean }>("/auth/logout", { method: "POST", body: JSON.stringify({}) });
  },
  me() {
    return request<MeResponse>("/auth/me");
  }
};

export const storesApi = {
  list() {
    return request<StoreSummary[]>("/stores");
  },
  create(payload: StoreCreateRequest) {
    return request<StoreSummary>("/stores", { method: "POST", body: JSON.stringify(payload) });
  },
  get(storeId: string) {
    return request<StoreSummary>(`/stores/${storeId}`);
  },
  getIntegration(storeId: string) {
    return request<IntegrationSummary>(`/stores/${storeId}/integration`);
  },
  createInstallUrl(storeId: string, redirect_uri: string) {
    return request<{ install_url: string; state: string }>(`/stores/${storeId}/shopify/install-url`, {
      method: "POST",
      body: JSON.stringify({ redirect_uri })
    });
  },
  createSyncRun(storeId: string, mode = "manual_full") {
    return request<SyncRunSummary>(`/stores/${storeId}/sync-runs`, {
      method: "POST",
      body: JSON.stringify({ mode })
    });
  },
  listSyncRuns(storeId: string) {
    return request<SyncRunSummary[]>(`/stores/${storeId}/sync-runs`);
  },
  getSyncRun(storeId: string, syncRunId: string) {
    return request<SyncRunSummary>(`/stores/${storeId}/sync-runs/${syncRunId}`);
  },
  retrySyncRun(storeId: string, syncRunId: string) {
    return request<SyncRunSummary>(`/stores/${storeId}/sync-runs/${syncRunId}/retry`, {
      method: "POST",
      body: JSON.stringify({})
    });
  },
  getDashboardSummary(storeId: string) {
    return request<DashboardSummaryResponse>(`/stores/${storeId}/dashboard/summary`);
  }
};

export const catalogApi = {
  listProducts(storeId: string) {
    return request<ProductSummary[]>(`/stores/${storeId}/products`);
  },
  getProduct(storeId: string, productId: string) {
    return request<ProductDetail>(`/stores/${storeId}/products/${productId}`);
  },
  listDrafts(storeId: string, productId: string) {
    return request<ProductDraftSummary[]>(`/stores/${storeId}/products/${productId}/content-drafts`);
  },
  getDraft(storeId: string, productId: string, draftId: string) {
    return request<ProductDraftSummary>(`/stores/${storeId}/products/${productId}/content-drafts/${draftId}`);
  },
  generateDraft(storeId: string, productId: string, payload: { generation_targets: string[]; tone: string; constraints: Record<string, unknown> }) {
    return request<DraftGenerationAcceptedResponse>(`/stores/${storeId}/products/${productId}/content-drafts/generate`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  updateDraft(storeId: string, productId: string, draftId: string, payload: Record<string, unknown>) {
    return request<ProductDraftSummary>(`/stores/${storeId}/products/${productId}/content-drafts/${draftId}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  },
  submitDraftForApproval(storeId: string, productId: string, draftId: string, reason: string) {
    return request<DraftApprovalSubmissionResponse>(`/stores/${storeId}/products/${productId}/content-drafts/${draftId}/submit-approval`, {
      method: "POST",
      body: JSON.stringify({ reason })
    });
  },
  listOrders(storeId: string) {
    return request<OrderSummary[]>(`/stores/${storeId}/orders`);
  },
  getOrder(storeId: string, orderId: string) {
    return request<OrderSummary>(`/stores/${storeId}/orders/${orderId}`);
  },
  listCustomers(storeId: string) {
    return request<CustomerSummary[]>(`/stores/${storeId}/customers`);
  },
  getCustomer(storeId: string, customerId: string) {
    return request<CustomerSummary>(`/stores/${storeId}/customers/${customerId}`);
  }
};

export const approvalsApi = {
  list() {
    return request<ApprovalResponse[]>("/approvals");
  },
  get(approvalId: string) {
    return request<ApprovalResponse>(`/approvals/${approvalId}`);
  },
  approve(approvalId: string, review_notes?: string) {
    return request<ApprovalActionResponse>(`/approvals/${approvalId}/approve`, {
      method: "POST",
      body: JSON.stringify({ review_notes })
    });
  },
  reject(approvalId: string, review_notes?: string) {
    return request<ApprovalActionResponse>(`/approvals/${approvalId}/reject`, {
      method: "POST",
      body: JSON.stringify({ review_notes })
    });
  },
  cancel(approvalId: string, review_notes?: string) {
    return request<ApprovalActionResponse>(`/approvals/${approvalId}/cancel`, {
      method: "POST",
      body: JSON.stringify({ review_notes })
    });
  },
  retryExecution(approvalId: string, review_notes?: string) {
    return request<ApprovalActionResponse>(`/approvals/${approvalId}/retry-execution`, {
      method: "POST",
      body: JSON.stringify({ review_notes })
    });
  }
};

export const supportApi = {
  listConversations(storeId: string, status?: string) {
    return request<SupportConversationResponse[]>(withQuery(`/stores/${storeId}/support/conversations`, { status }));
  },
  createConversation(storeId: string, payload: Record<string, unknown>) {
    return request<SupportConversationResponse>(`/stores/${storeId}/support/conversations`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  getConversation(storeId: string, conversationId: string) {
    return request<SupportConversationResponse>(`/stores/${storeId}/support/conversations/${conversationId}`);
  },
  updateConversation(storeId: string, conversationId: string, status: string) {
    return request<SupportConversationResponse>(`/stores/${storeId}/support/conversations/${conversationId}`, {
      method: "PATCH",
      body: JSON.stringify({ status })
    });
  },
  listMessages(storeId: string, conversationId: string) {
    return request<SupportMessageResponse[]>(`/stores/${storeId}/support/conversations/${conversationId}/messages`);
  },
  createMessage(storeId: string, conversationId: string, payload: { direction: string; body: string }) {
    return request<SupportMessageResponse>(`/stores/${storeId}/support/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  generateDraft(storeId: string, conversationId: string, force_policy_type?: string) {
    return request<SupportDraftGenerationAcceptedResponse>(`/stores/${storeId}/support/conversations/${conversationId}/reply-drafts/generate`, {
      method: "POST",
      body: JSON.stringify({ force_policy_type })
    });
  }
};

export const policiesApi = {
  list(storeId: string) {
    return request<PolicyDocumentResponse[]>(`/stores/${storeId}/policies`);
  },
  create(storeId: string, payload: Record<string, unknown>) {
    return request<PolicyDocumentResponse>(`/stores/${storeId}/policies`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  get(storeId: string, policyId: string) {
    return request<PolicyDocumentResponse>(`/stores/${storeId}/policies/${policyId}`);
  },
  update(storeId: string, policyId: string, payload: Record<string, unknown>) {
    return request<PolicyDocumentResponse>(`/stores/${storeId}/policies/${policyId}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
  }
};

export const fraudApi = {
  getOrderRiskScore(storeId: string, orderId: string) {
    return request<OrderRiskScoreResponse>(`/stores/${storeId}/orders/${orderId}/risk-score`);
  },
  listRiskReviews(storeId: string, risk_status?: string) {
    return request<RiskReviewResponse[]>(withQuery(`/stores/${storeId}/risk-reviews`, { risk_status }));
  },
  getRiskReview(storeId: string, riskReviewId: string) {
    return request<RiskReviewResponse>(`/stores/${storeId}/risk-reviews/${riskReviewId}`);
  },
  recordDecision(storeId: string, riskReviewId: string, decision: string, decision_notes?: string) {
    return request<RiskReviewResponse>(`/stores/${storeId}/risk-reviews/${riskReviewId}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision, decision_notes })
    });
  }
};

export const inventoryApi = {
  listAlerts(storeId: string, status?: string) {
    return request<InventoryAlertResponse[]>(withQuery(`/stores/${storeId}/inventory/alerts`, { status }));
  },
  listSuggestions(storeId: string, status?: string) {
    return request<ReorderSuggestionResponse[]>(withQuery(`/stores/${storeId}/inventory/reorder-suggestions`, { status }));
  },
  getSuggestion(storeId: string, suggestionId: string) {
    return request<ReorderSuggestionResponse>(`/stores/${storeId}/inventory/reorder-suggestions/${suggestionId}`);
  },
  createOrRefreshSupplierDraft(storeId: string, suggestionId: string, payload: Record<string, unknown>) {
    return request<ReorderSuggestionResponse>(`/stores/${storeId}/inventory/reorder-suggestions/${suggestionId}/supplier-drafts`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }
};

export const analyticsApi = {
  getOverview(storeId: string, query?: { date_from?: string; date_to?: string }) {
    return request<AnalyticsOverviewResponse>(withQuery(`/stores/${storeId}/analytics/overview`, query));
  },
  getAutomation(storeId: string, query?: { date_from?: string; date_to?: string }) {
    return request<AnalyticsAutomationResponse>(withQuery(`/stores/${storeId}/analytics/automation`, query));
  }
};

export const orgApi = {
  getCurrent() {
    return request<OrganizationResponse>("/organizations/current");
  },
  create(payload: OrganizationCreateRequest) {
    return request<OrganizationResponse>("/organizations", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }
};

export const usersApi = {
  list(query?: { status?: string; role?: string; q?: string }) {
    return request<UserResponse[]>(withQuery("/users", query));
  },
  create(payload: CreateUserRequest) {
    return request<UserResponse>("/users", { method: "POST", body: JSON.stringify(payload) });
  },
  update(userId: string, payload: UpdateUserRequest) {
    return request<UserResponse>(`/users/${userId}`, { method: "PATCH", body: JSON.stringify(payload) });
  },
  listRoles() {
    return request<RoleSummary[]>("/roles");
  }
};

export const notificationsApi = {
  list(query?: { status?: string; type?: string; store_id?: string }) {
    return request<NotificationSummary[]>(withQuery("/notifications", query));
  },
  markRead(notificationId: string) {
    return request<NotificationSummary>(`/notifications/${notificationId}/read`, {
      method: "PATCH",
      body: JSON.stringify({})
    });
  }
};

export const runtimeApi = {
  listWorkflowRuns(storeId: string, query?: { status?: string; workflow_key?: string; trigger_type?: string }) {
    return request<WorkflowRunSummary[]>(withQuery(`/stores/${storeId}/workflow-runs`, query));
  },
  getWorkflowRun(storeId: string, workflowRunId: string) {
    return request<WorkflowRunSummary>(`/stores/${storeId}/workflow-runs/${workflowRunId}`);
  },
  listAgentRuns(storeId: string, query?: { agent_type?: string; status?: string; workflow_run_id?: string }) {
    return request<AgentRunSummary[]>(withQuery(`/stores/${storeId}/agent-runs`, query));
  },
  getAgentRun(storeId: string, agentRunId: string) {
    return request<AgentRunSummary>(`/stores/${storeId}/agent-runs/${agentRunId}`);
  },
  listAuditEvents(storeId: string, query?: { entity_type?: string; action_type?: string; user_id?: string }) {
    return request<AuditEventSummary[]>(withQuery(`/stores/${storeId}/audit-events`, query));
  }
};

export { ApiError };
