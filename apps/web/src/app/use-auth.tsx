import * as React from "react";

import { authApi, configureApiAuth } from "@frontend/api-client";
import type { AuthTokenResponse, MeResponse } from "@frontend/types";

type AuthContextValue = {
  accessToken: string | null;
  me: MeResponse | null;
  initialized: boolean;
  isAuthenticated: boolean;
  login: (payload: { email: string; password: string }) => Promise<void>;
  register: (payload: { email: string; password: string; full_name: string }) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<string | null>;
  reloadMe: () => Promise<void>;
};

const AuthContext = React.createContext<AuthContextValue | null>(null);

async function toSession(result: AuthTokenResponse, setAccessToken: (token: string | null) => void) {
  setAccessToken(result.access_token);
}

export function AuthProvider({ children }: React.PropsWithChildren) {
  const [accessToken, setAccessToken] = React.useState<string | null>(null);
  const [me, setMe] = React.useState<MeResponse | null>(null);
  const [initialized, setInitialized] = React.useState(false);

  const reloadMe = React.useCallback(async () => {
    const data = await authApi.me();
    setMe(data);
  }, []);

  const refreshSession = React.useCallback(async () => {
    try {
      const result = await authApi.refresh();
      await toSession(result, setAccessToken);
      return result.access_token;
    } catch {
      setAccessToken(null);
      setMe(null);
      return null;
    }
  }, []);

  React.useEffect(() => {
    configureApiAuth({
      getAccessToken: () => accessToken,
      refreshAccessToken: refreshSession
    });
  }, [accessToken, refreshSession]);

  React.useEffect(() => {
    let active = true;
    (async () => {
      const token = await refreshSession();
      if (token && active) {
        try {
          await reloadMe();
        } catch {
          setMe(null);
        }
      }
      if (active) setInitialized(true);
    })();
    return () => {
      active = false;
    };
  }, [refreshSession, reloadMe]);

  const login = React.useCallback(
    async (payload: { email: string; password: string }) => {
      const result = await authApi.login(payload);
      await toSession(result, setAccessToken);
      await reloadMe();
    },
    [reloadMe]
  );

  const register = React.useCallback(
    async (payload: { email: string; password: string; full_name: string }) => {
      const result = await authApi.register(payload);
      await toSession(result, setAccessToken);
      await reloadMe();
    },
    [reloadMe]
  );

  const logout = React.useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setAccessToken(null);
      setMe(null);
    }
  }, []);

  const value = React.useMemo<AuthContextValue>(
    () => ({
      accessToken,
      me,
      initialized,
      isAuthenticated: Boolean(accessToken && me),
      login,
      register,
      logout,
      refreshSession,
      reloadMe
    }),
    [accessToken, me, initialized, login, register, logout, refreshSession, reloadMe]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
