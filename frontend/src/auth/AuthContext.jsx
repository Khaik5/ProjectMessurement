import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { authService } from './authService.js';
import { clearToken, getToken, setToken as persistToken } from './tokenStorage.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(getToken());
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(getToken()));

  async function bootstrap() {
    const stored = getToken();
    if (!stored) {
      setLoading(false);
      return;
    }
    try {
      const current = await authService.me();
      setUser(current);
      setToken(stored);
    } catch {
      clearToken();
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    bootstrap();
    const handler = () => {
      clearToken();
      setToken(null);
      setUser(null);
    };
    window.addEventListener('defectai:logout', handler);
    return () => window.removeEventListener('defectai:logout', handler);
  }, []);

  async function login(username, password) {
    const result = await authService.login({ username, password });
    persistToken(result.access_token);
    setToken(result.access_token);
    setUser(result.user);
    return result.user;
  }

  async function logout() {
    try {
      if (getToken()) await authService.logout();
    } catch {
      // Token may already be expired; local logout still wins.
    }
    clearToken();
    setToken(null);
    setUser(null);
  }

  function hasRole(role) {
    return Boolean(user?.roles?.includes(role));
  }

  function hasPermission(permission) {
    if (!permission) return true;
    if (hasRole('Admin')) return true;
    const permissions = Array.isArray(permission) ? permission : [permission];
    return permissions.some((item) => user?.permissions?.includes(item));
  }

  const value = useMemo(
    () => ({ token, user, loading, login, logout, hasRole, hasPermission }),
    [token, user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}

