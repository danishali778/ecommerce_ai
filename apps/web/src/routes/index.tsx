import * as React from "react";
import { Navigate, Outlet, Route, Routes, useLocation, useParams } from "react-router-dom";

import { useAppState } from "@/hooks/use-app-state";
import { useAuth } from "@/hooks/use-auth";
import { AppShell, PublicShell } from "@/components/shell";

function routeLoader<T extends Record<string, React.ComponentType<any>>, K extends keyof T>(
  factory: () => Promise<T>,
  key: K
) {
  return React.lazy(async () => {
    const module = await factory();
    return { default: module[key] };
  });
}

const LandingPage = routeLoader(() => import("@/pages/public-pages"), "LandingPage");
const LoginPage = routeLoader(() => import("@/pages/public-pages"), "LoginPage");
const SignupPage = routeLoader(() => import("@/pages/public-pages"), "SignupPage");
const DashboardPage = routeLoader(() => import("@/pages/stores-pages"), "DashboardPage");
const StoreListPage = routeLoader(() => import("@/pages/stores-pages"), "StoreListPage");
const StoreDetailPage = routeLoader(() => import("@/pages/stores-pages"), "StoreDetailPage");
const StoreIntegrationPage = routeLoader(() => import("@/pages/stores-pages"), "StoreIntegrationPage");
const StoreSyncRunsPage = routeLoader(() => import("@/pages/stores-pages"), "StoreSyncRunsPage");
const CatalogPage = routeLoader(() => import("@/pages/catalog-pages"), "CatalogPage");
const ProductDetailPage = routeLoader(() => import("@/pages/catalog-pages"), "ProductDetailPage");
const ApprovalsPage = routeLoader(() => import("@/pages/approvals-pages"), "ApprovalsPage");
const ApprovalDetailPage = routeLoader(() => import("@/pages/approvals-pages"), "ApprovalDetailPage");
const SupportPage = routeLoader(() => import("@/pages/support-pages"), "SupportPage");
const SupportConversationPage = routeLoader(() => import("@/pages/support-pages"), "SupportConversationPage");
const PoliciesPage = routeLoader(() => import("@/pages/support-pages"), "PoliciesPage");
const FraudPage = routeLoader(() => import("@/pages/fraud-pages"), "FraudPage");
const FraudDetailPage = routeLoader(() => import("@/pages/fraud-pages"), "FraudDetailPage");
const InventoryPage = routeLoader(() => import("@/pages/inventory-pages"), "InventoryPage");
const AnalyticsOverviewPage = routeLoader(() => import("@/pages/analytics-pages"), "AnalyticsOverviewPage");
const AnalyticsAutomationPage = routeLoader(() => import("@/pages/analytics-pages"), "AnalyticsAutomationPage");
const NotificationsPage = routeLoader(() => import("@/pages/admin-pages"), "NotificationsPage");
const OrganizationPage = routeLoader(() => import("@/pages/admin-pages"), "OrganizationPage");
const UsersPage = routeLoader(() => import("@/pages/admin-pages"), "UsersPage");
const UserDetailPage = routeLoader(() => import("@/pages/admin-pages"), "UserDetailPage");
const RuntimeWorkflowRunsPage = routeLoader(() => import("@/pages/runtime-pages"), "RuntimeWorkflowRunsPage");
const RuntimeAgentRunsPage = routeLoader(() => import("@/pages/runtime-pages"), "RuntimeAgentRunsPage");
const RuntimeAuditPage = routeLoader(() => import("@/pages/runtime-pages"), "RuntimeAuditPage");

function RouteSuspense({ children }: { children: React.ReactNode }) {
  return (
    <React.Suspense
      fallback={<div className="flex min-h-[40vh] items-center justify-center text-slate-500">Loading workspace…</div>}
    >
      {children}
    </React.Suspense>
  );
}

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
    <RouteSuspense>
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
    </RouteSuspense>
  );
}
