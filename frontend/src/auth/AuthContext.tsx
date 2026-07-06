import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../api/endpoints";
import { clearToken, getToken, setToken } from "../api/client";
import type { UserPublic } from "../api/types";

interface AuthState {
  user: UserPublic | null;
  loading: boolean;
  soloMode: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, displayName: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [soloMode, setSoloMode] = useState(false);

  useEffect(() => {
    let cancelled = false;
    // Solo mode: no login — /auth/me resolves the single local profile without a
    // token, so we go straight into the curriculum. Hosted mode: token flow.
    const tokenFlow = () => {
      if (!getToken()) {
        setLoading(false);
        return;
      }
      api.me().then((u) => !cancelled && setUser(u)).catch(() => clearToken()).finally(
        () => !cancelled && setLoading(false),
      );
    };
    api
      .config()
      .then((cfg) => {
        if (cancelled) return;
        if (cfg.solo_mode) {
          setSoloMode(true);
          api.me().then((u) => !cancelled && setUser(u)).catch(() => undefined).finally(
            () => !cancelled && setLoading(false),
          );
        } else {
          tokenFlow();
        }
      })
      .catch(tokenFlow);
    return () => {
      cancelled = true;
    };
  }, []);

  async function login(email: string, password: string) {
    const { access_token } = await api.login(email, password);
    setToken(access_token);
    setUser(await api.me());
  }

  async function register(email: string, displayName: string, password: string) {
    await api.register(email, displayName, password);
    await login(email, password);
  }

  function logout() {
    clearToken();
    setUser(null);
  }

  const value = useMemo(
    () => ({ user, loading, soloMode, login, register, logout }),
    [user, loading, soloMode],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
