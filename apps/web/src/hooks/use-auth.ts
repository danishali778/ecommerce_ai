import * as React from "react";

import { AuthContext } from "@/providers/auth-provider";

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
