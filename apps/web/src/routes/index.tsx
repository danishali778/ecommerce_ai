import { Navigate, Outlet, Route, Routes, useLocation, useParams } from "react-router-dom";

import { useAppState } from "@/app/use-app-state";
import { useAuth } from "@/app/use-auth";
import { AppShell, PublicShell } from "@/components/shell";
import {
  AnalyticsAutomationPage,
  AnalyticsOverviewPage,
  ApprovalDetailPage,
  ApprovalsPage,
  CatalogPage,
  DashboardPage,
  FraudDetailPage,
  FraudPage,
  InventoryPage,
  LandingPage,
  LoginPage,
  NotificationsPage,
  OrganizationPage,
  PoliciesPage,
  ProductDetailPage,
  RuntimeAgentRunsPage,
  RuntimeAuditPage,
  RuntimeWorkflowRunsPage,
  SignupPage,
  StoreDetailPage,
  StoreIntegrationPage,
  StoreListPage,
  StoreSyncRunsPage,
  SupportConversationPage,
  SupportPage,
  UserDetailPage,
  UsersPage
} from "@/pages";

function ProtectedRoute() {
  const { initialized, isAuthenticated } = useAuth();
  const location = useLocation();
  if (!initialized) {
    return <div className="flex min-h-screen items-center justify-center text-slate-500">Loading session…</div>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

function StoreAwareRedirect({
  makePath
}: {
  makePath: (storeId: string) => string;
}) {
  const { selectedStoreId } = useAppState();
  if (!selectedStoreId) return <Navigate to="/app/stores" replace />;
  return <Navigate to={makePath(selectedStoreId)} replace />;
}

function RuntimeRedirect() {
  const { selectedStoreId } = useAppState();
  if (!selectedStoreId) return <Navigate to="/app/stores" replace />;
  return <Navigate to={`/app/runtime/workflows/${selectedStoreId}`} replace />;
}

function AnalyticsRedirect() {
  return <StoreAwareRedirect makePath={(storeId) => `/app/analytics/${storeId}`} />;
}

function CatalogRedirect() {
  return <StoreAwareRedirect makePath={(storeId) => `/app/catalog/${storeId}/products`} />;
}

function SupportRedirect() {
  return <StoreAwareRedirect makePath={(storeId) => `/app/support/${storeId}/conversations`} />;
}

function FraudRedirect() {
  return <StoreAwareRedirect makePath={(storeId) => `/app/fraud/${storeId}/reviews`} />;
}

function InventoryRedirect() {
  return <StoreAwareRedirect makePath={(storeId) => `/app/inventory/${storeId}`} />;
}

function AnalyticsAutomationRedirect() {
  const { storeId } = useParams();
  return storeId ? <AnalyticsAutomationPage /> : <Navigate to="/app/analytics" replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <PublicShell>
            <LandingPage />
          </PublicShell>
        }
      />
      <Route
        path="/login"
        element={
          <PublicShell>
            <LoginPage />
          </PublicShell>
        }
      />
      <Route
        path="/signup"
        element={
          <PublicShell>
            <SignupPage />
          </PublicShell>
        }
      />

      <Route path="/app" element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="stores" element={<StoreListPage />} />
          <Route path="stores/:storeId" element={<StoreDetailPage />} />
          <Route path="stores/:storeId/integration" element={<StoreIntegrationPage />} />
          <Route path="stores/:storeId/sync-runs" element={<StoreSyncRunsPage />} />

          <Route path="catalog" element={<CatalogRedirect />} />
          <Route path="catalog/:storeId/products" element={<CatalogPage />} />
          <Route path="catalog/:storeId/products/:productId" element={<ProductDetailPage />} />

          <Route path="approvals" element={<ApprovalsPage />} />
          <Route path="approvals/:approvalId" element={<ApprovalDetailPage />} />

          <Route path="support" element={<SupportRedirect />} />
          <Route path="support/:storeId/conversations" element={<SupportPage />} />
          <Route path="support/:storeId/conversations/:conversationId" element={<SupportConversationPage />} />
          <Route path="support/:storeId/policies" element={<PoliciesPage />} />

          <Route path="fraud" element={<FraudRedirect />} />
          <Route path="fraud/:storeId/reviews" element={<FraudPage />} />
          <Route path="fraud/:storeId/reviews/:riskReviewId" element={<FraudDetailPage />} />

          <Route path="inventory" element={<InventoryRedirect />} />
          <Route path="inventory/:storeId" element={<InventoryPage />} />

          <Route path="analytics" element={<AnalyticsRedirect />} />
          <Route path="analytics/:storeId" element={<AnalyticsOverviewPage />} />
          <Route path="analytics/:storeId/automation" element={<AnalyticsAutomationRedirect />} />

          <Route path="notifications" element={<NotificationsPage />} />
          <Route path="organization" element={<OrganizationPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="users/:userId" element={<UserDetailPage />} />

          <Route path="runtime" element={<RuntimeRedirect />} />
          <Route path="runtime/workflows/:storeId" element={<RuntimeWorkflowRunsPage />} />
          <Route path="runtime/agents/:storeId" element={<RuntimeAgentRunsPage />} />
          <Route path="runtime/audit/:storeId" element={<RuntimeAuditPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
