import * as React from "react";

import { useAuth } from "@/app/use-auth";

type AppStateContextValue = {
  selectedStoreId: string | null;
  setSelectedStoreId: (storeId: string | null) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
};

const STORAGE_KEY = "commerceops:selected-store";
const AppStateContext = React.createContext<AppStateContextValue | null>(null);

export function AppStateProvider({ children }: React.PropsWithChildren) {
  const { me } = useAuth();
  const [selectedStoreId, setSelectedStoreIdState] = React.useState<string | null>(() => localStorage.getItem(STORAGE_KEY));
  const [sidebarOpen, setSidebarOpen] = React.useState(true);

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

  return (
    <AppStateContext.Provider value={{ selectedStoreId, setSelectedStoreId, sidebarOpen, setSidebarOpen }}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const context = React.useContext(AppStateContext);
  if (!context) throw new Error("useAppState must be used within AppStateProvider");
  return context;
}
