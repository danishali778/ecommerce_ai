import * as React from "react";

import { useAuth } from "@/hooks/use-auth";

export type AppStateContextValue = {
  selectedStoreId: string | null;
  setSelectedStoreId: (storeId: string | null) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
};

const STORAGE_KEY = "commerceops:selected-store";

export const AppStateContext = React.createContext<AppStateContextValue | null>(null);

export function AppStateProvider({ children }: React.PropsWithChildren) {
  const { me } = useAuth();
  const [selectedStoreId, setSelectedStoreIdState] = React.useState<string | null>(() => localStorage.getItem(STORAGE_KEY));
  const [sidebarOpen, setSidebarOpen] = React.useState(() => {
    if (typeof window === "undefined") return true;
    return window.innerWidth >= 1024;
  });

  React.useEffect(() => {
    if (!me?.accessible_stores?.length) return;
    if (selectedStoreId && me.accessible_stores.some((store) => store.id === selectedStoreId)) return;
    const next = me.accessible_stores[0]?.id ?? null;
    setSelectedStoreIdState(next);
  }, [me, selectedStoreId]);

  const setSelectedStoreId = React.useCallback((storeId: string | null) => {
    setSelectedStoreIdState(storeId);
    if (storeId) {
      localStorage.setItem(STORAGE_KEY, storeId);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const value = React.useMemo(
    () => ({ selectedStoreId, setSelectedStoreId, sidebarOpen, setSidebarOpen }),
    [selectedStoreId, setSelectedStoreId, sidebarOpen]
  );

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}
