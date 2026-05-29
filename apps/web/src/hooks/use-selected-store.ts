import { useMemo } from "react";

import { useAppState } from "@/hooks/use-app-state";
import { useAuth } from "@/hooks/use-auth";

export function useSelectedStore() {
  const { me } = useAuth();
  const { selectedStoreId, setSelectedStoreId } = useAppState();

  const selectedStore = useMemo(
    () => me?.accessible_stores.find((store) => store.id === selectedStoreId) ?? null,
    [me, selectedStoreId]
  );

  return {
    selectedStoreId,
    selectedStore,
    setSelectedStoreId
  };
}
