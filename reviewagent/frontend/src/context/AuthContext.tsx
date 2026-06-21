import React, { createContext, useContext, useState } from 'react';
import { jwtDecode } from 'jwt-decode';

interface JwtPayload {
  role: string;
  name: string;
  exp: number;
}

interface User {
  role: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

function loadUserFromStorage(): User | null {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    const decoded = jwtDecode<JwtPayload>(token);
    if (decoded.exp * 1000 > Date.now()) {
      return { role: decoded.role, name: decoded.name };
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  } catch {}
  return null;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(loadUserFromStorage);

  const login = (accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    const decoded = jwtDecode<JwtPayload>(accessToken);
    setUser({ role: decoded.role, name: decoded.name });
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
