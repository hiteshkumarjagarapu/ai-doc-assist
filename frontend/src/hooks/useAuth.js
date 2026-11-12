import { createContext, createElement, useCallback, useContext, useMemo, useState } from "react";
import api from "../api/api";

const AuthContext = createContext(null);

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("user"));
  } catch {
    return null;
  }
}

/** Provides auth state (token, user) and login/register/logout to the app. */
export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(readStoredUser);

  const saveSession = useCallback((data) => {
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  }, []);

  const login = useCallback(
    async (email, password) => {
      const { data } = await api.post("/auth/login", { email, password });
      saveSession(data);
    },
    [saveSession]
  );

  const register = useCallback(
    async (name, email, password) => {
      const { data } = await api.post("/auth/register", { name, email, password });
      saveSession(data);
    },
    [saveSession]
  );

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ token, user, isAuthenticated: !!token, login, register, logout }),
    [token, user, login, register, logout]
  );

  return createElement(AuthContext.Provider, { value }, children);
}

/** Access auth state and actions. */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
