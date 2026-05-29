import * as React from "react";

import { AppStateContext } from "@/providers/app-state-provider";

export function useAppState() {
  const context = React.useContext(AppStateContext);
  if (!context) throw new Error("useAppState must be used within AppStateProvider");
  return context;
}
