import { useQuery } from "@tanstack/react-query";

import { runtimeApi } from "@frontend/api-client";

export function useWorkflowRuns(storeId: string, query?: { status?: string; workflow_key?: string; trigger_type?: string }) {
  return useQuery({
    queryKey: ["runtime", "workflow-runs", storeId, query?.status ?? "", query?.workflow_key ?? "", query?.trigger_type ?? ""],
    queryFn: () => runtimeApi.listWorkflowRuns(storeId, query),
    enabled: Boolean(storeId)
  });
}

export function useWorkflowRun(storeId: string, workflowRunId: string | null) {
  return useQuery({
    queryKey: ["runtime", "workflow-run", storeId, workflowRunId],
    queryFn: () => runtimeApi.getWorkflowRun(storeId, workflowRunId!),
    enabled: Boolean(storeId && workflowRunId)
  });
}

export function useAgentRuns(storeId: string, query?: { agent_type?: string; status?: string; workflow_run_id?: string }) {
  return useQuery({
    queryKey: ["runtime", "agent-runs", storeId, query?.agent_type ?? "", query?.status ?? "", query?.workflow_run_id ?? ""],
    queryFn: () => runtimeApi.listAgentRuns(storeId, query),
    enabled: Boolean(storeId)
  });
}

export function useAgentRun(storeId: string, agentRunId: string | null) {
  return useQuery({
    queryKey: ["runtime", "agent-run", storeId, agentRunId],
    queryFn: () => runtimeApi.getAgentRun(storeId, agentRunId!),
    enabled: Boolean(storeId && agentRunId)
  });
}

export function useAuditEvents(storeId: string, query?: { entity_type?: string; action_type?: string; user_id?: string }) {
  return useQuery({
    queryKey: ["runtime", "audit-events", storeId, query?.entity_type ?? "", query?.action_type ?? "", query?.user_id ?? ""],
    queryFn: () => runtimeApi.listAuditEvents(storeId, query),
    enabled: Boolean(storeId)
  });
}
