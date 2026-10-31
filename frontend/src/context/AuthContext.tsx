import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, UserRole } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  demoLogin: (role: UserRole) => Promise<void>;
  logout: () => void;
}

const DEMO_CREDENTIALS: Record<UserRole, { email: string; pass: string }> = {
  admin: { email: 'admin@cit.edu', pass: 'Admin@123' },
  coordinator: { email: 'coordinator@cit.edu', pass: 'Coord@123' },
  faculty: { email: 'faculty@cit.edu', pass: 'Faculty@123' },
  club: { email: 'club@cit.edu', pass: 'Club@123' },
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => api.getToken());
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    api.setOnAuthError(() => {
      setUser(null);
      setToken(null);
    });

    const initAuth = async () => {
      const existingToken = api.getToken();
      if (existingToken) {
        try {
          const profile = await api.getMe();
          setUser(profile);
          setToken(existingToken);
        } catch {
          api.setToken(null);
          setUser(null);
          setToken(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const res = await api.login(email, password);
      setUser(res.user);
      setToken(res.access_token);
    } finally {
      setLoading(false);
    }
  };

  const demoLogin = async (role: UserRole) => {
    const creds = DEMO_CREDENTIALS[role];
    if (creds) {
      await login(creds.email, creds.pass);
    }
  };

  const logout = () => {
    api.setToken(null);
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, demoLogin, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
