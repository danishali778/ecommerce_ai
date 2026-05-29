const viteEnv = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;

export const appConfig = {
  appName: "CommerceOps AI",
  apiBaseUrl: viteEnv?.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
};

export const runtimeFilters = {
  workflowStatus: ["queued", "running", "succeeded", "failed"],
  supportStatus: ["open", "pending_review", "resolved"],
  notificationStatus: ["unread", "read"]
} as const;
