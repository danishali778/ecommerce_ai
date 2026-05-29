export interface PaginationMeta {
  request_id?: string | null;
  timestamp: string;
  next_cursor?: string | null;
  count?: number | null;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: PaginationMeta;
}

export interface StoreSummary {
  id: string;
  name: string;
  platform: string;
  domain: string;
  currency?: string | null;
  timezone?: string | null;
  connection_status: string;
  last_successful_sync_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IntegrationSummary {
  provider: string;
  scopes: string[];
  status: string;
  last_successful_sync_at?: string | null;
}

export interface SyncRunSummary {
  id: string;
  status: string;
  mode: string;
  records_imported: number;
  records_failed: number;
  entity_counts_json: Record<string, unknown>;
  error_summary?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  retry_of_sync_run_id?: string | null;
  created_at: string;
}

export interface ProductVariantSummary {
  id: string;
  external_variant_id: string;
  sku?: string | null;
  title: string;
  price: string;
  compare_at_price?: string | null;
  inventory_quantity: number;
}

export interface ProductDraftSummary {
  id: string;
  product_id: string;
  generated_title?: string | null;
  generated_description?: string | null;
  generated_tags: string[];
  generated_seo_title?: string | null;
  generated_seo_description?: string | null;
  model_name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ProductSummary {
  id: string;
  title: string;
  handle: string;
  vendor?: string | null;
  status: string;
  seo_title?: string | null;
  inventory_total: number;
  updated_at: string;
}

export interface ProductDetail extends ProductSummary {
  variants: ProductVariantSummary[];
  latest_draft?: ProductDraftSummary | null;
}

export interface OrderSummary {
  id: string;
  external_order_id: string;
  status: string;
  payment_status?: string | null;
  fulfillment_status?: string | null;
  total: string;
  currency?: string | null;
  created_at: string;
}

export interface CustomerSummary {
  id: string;
  email?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  total_orders: number;
  created_at: string;
}

export interface DashboardSummaryResponse {
  latest_sync_status?: string | null;
  latest_sync_completed_at?: string | null;
  product_count: number;
  order_count: number;
  customer_count: number;
  low_inventory_count: number;
  pending_approval_count: number;
  recent_workflow_failures: number;
  recent_agent_runs: number;
}

export interface ApprovalSummary {
  id: string;
  status: string;
  action_type: string;
  entity_type: string;
  entity_id: string;
  reasoning: string;
  review_notes?: string | null;
  execution_status?: string | null;
  execution_error?: string | null;
  expires_at: string;
  created_at: string;
  updated_at: string;
}

export type ApprovalResponse = ApprovalSummary;
export type ApprovalActionResponse = ApprovalSummary;

export interface WorkflowRunSummary {
  id: string;
  status: string;
  trigger_type: string;
  workflow_id?: string | null;
  created_at: string;
  input_payload?: Record<string, unknown> | null;
  output_payload?: Record<string, unknown> | null;
  error_message?: string | null;
}

export interface AgentRunSummary {
  id: string;
  status: string;
  agent_type: string;
  model_name: string;
  created_at: string;
  workflow_run_id?: string | null;
  input_summary?: string | null;
  retrieved_context_summary?: string | null;
  output_summary?: string | null;
  error_message?: string | null;
}

export interface AuditEventSummary {
  id: string;
  entity_type: string;
  action_type: string;
  source_type: string;
  outcome: string;
  created_at: string;
  user_id?: string | null;
  metadata_json?: Record<string, unknown> | null;
}

export interface NotificationSummary {
  id: string;
  type: string;
  channel: string;
  title: string;
  body: string;
  status: string;
  read_at?: string | null;
  created_at: string;
  store_id?: string | null;
}

export interface RoleSummary {
  name: string;
  description: string;
  permissions: string[];
}

export interface UserSummary {
  id: string;
  email: string;
  full_name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface UserResponse extends UserSummary {
  roles: string[];
}

export interface OrganizationResponse {
  id: string;
  name: string;
  slug: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user?: Record<string, unknown> | null;
  organization?: Record<string, unknown> | null;
  available_roles: string[];
}

export interface MeUserContext {
  id: string;
  email: string;
  full_name: string;
  status: string;
}

export interface MeOrganizationContext {
  id: string;
  name: string;
  slug: string;
  status: string;
}

export interface MeResponse {
  user: MeUserContext;
  organization?: MeOrganizationContext | null;
  roles: string[];
  permissions: string[];
  accessible_stores: StoreSummary[];
  available_role_summaries: RoleSummary[];
}

export interface PolicyDocumentResponse {
  id: string;
  store_id: string;
  document_type: string;
  source_type: string;
  title: string;
  content: string;
  version?: string | null;
  is_active: boolean;
  embedding_status: string;
  created_at: string;
  updated_at: string;
}

export interface SupportConversationResponse {
  id: string;
  store_id: string;
  customer_id?: string | null;
  order_id?: string | null;
  external_ticket_id?: string | null;
  channel: string;
  status: string;
  assigned_user_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SupportMessageResponse {
  id: string;
  conversation_id: string;
  direction: string;
  body: string;
  generated_by_ai: boolean;
  confidence_score?: number | null;
  needs_human_review: boolean;
  review_reason_code?: string | null;
  status: string;
  cited_policy_chunks_json: Array<Record<string, unknown>>;
  cited_order_facts_summary?: string | null;
  created_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SupportDraftGenerationAcceptedResponse {
  workflow_run_id: string;
  agent_run_id: string;
  status: string;
}

export interface OrderRiskScoreResponse {
  order_id: string;
  risk_score: number;
  risk_status: string;
}

export interface RiskReviewResponse {
  id: string;
  order_id: string;
  risk_score: number;
  risk_status: string;
  reason_codes_json: string[];
  decision?: string | null;
  decision_notes?: string | null;
  reviewed_by_user_id?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InventoryAlertResponse {
  id: string;
  product_id: string;
  variant_id: string;
  threshold_value: number;
  current_quantity: number;
  status: string;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SupplierReorderDraftResponse {
  id: string;
  vendor_name: string;
  recipient_email?: string | null;
  subject: string;
  body: string;
  status: string;
  created_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReorderSuggestionResponse {
  id: string;
  inventory_alert_id: string;
  product_id: string;
  variant_id?: string | null;
  recommended_quantity: number;
  current_quantity: number;
  threshold_value: number;
  rationale_json: Record<string, unknown>;
  status: string;
  created_at: string;
  updated_at: string;
  supplier_draft?: SupplierReorderDraftResponse | null;
}

export interface AnalyticsRangeResponse {
  date_from: string;
  date_to: string;
}

export interface AnalyticsErrorResponse {
  section: string;
  message: string;
}

export interface AnalyticsOverviewResponse {
  range: AnalyticsRangeResponse;
  generated_at: string;
  sections: {
    sales: Record<string, unknown>;
    inventory: Record<string, unknown>;
    support: Record<string, unknown>;
    fraud: Record<string, unknown>;
    operations: Record<string, unknown>;
  };
  partial_errors?: AnalyticsErrorResponse[] | null;
}

export interface AnalyticsAutomationResponse {
  range: AnalyticsRangeResponse;
  generated_at: string;
  sections: Record<string, unknown>;
  partial_errors?: AnalyticsErrorResponse[] | null;
}

export interface DraftGenerationAcceptedResponse {
  agent_run_id: string;
  workflow_run_id: string;
  status: string;
}

export interface DraftApprovalSubmissionResponse {
  approval_id: string;
  approval_status: string;
  draft_status: string;
}

export interface InstallUrlResponse {
  install_url: string;
  state: string;
}

export interface CreateUserRequest {
  email: string;
  full_name: string;
  role_names: string[];
}

export interface UpdateUserRequest {
  full_name?: string;
  status?: string;
  role_names?: string[];
}

export interface OrganizationCreateRequest {
  name: string;
  slug: string;
}

export interface StoreCreateRequest {
  name: string;
  platform?: string;
  domain: string;
  currency?: string | null;
  timezone?: string | null;
}
