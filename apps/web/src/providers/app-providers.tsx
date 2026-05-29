import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as React from "react";

import { AppStateProvider } from "@/providers/app-state-provider";
import { AuthProvider } from "@/providers/auth-provider";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 30_000
    }
  }
});

export function AppProviders({ children }: React.PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppStateProvider>{children}</AppStateProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
