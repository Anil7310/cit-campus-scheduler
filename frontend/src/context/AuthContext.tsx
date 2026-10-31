import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, UserRole } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (usernameOrEmail: string, password: string, role?: string) => Promise<User>;
  demoLogin: (role: UserRole) => Promise<User>;
  logout: () => void;
}

export const DEMO_CREDENTIALS: Record<UserRole, { username: string; email: string; pass: string; title: string; subtitle: string }> = {
  admin: { username: 'admin', email: 'admin@cit.edu', pass: 'Admin@123', title: 'System Administrator', subtitle: 'Dean\'s Office (Full control & member creation)' },
  faculty: { username: 'faculty', email: 'faculty@cit.edu', pass: 'Faculty@123', title: 'Faculty Member', subtitle: 'Dr. A. Sharma (Timetable, reschedule & batch matching)' },
  coordinator: { username: 'coordinator', email: 'coordinator@cit.edu', pass: 'Coord@123', title: 'Academic Coordinator', subtitle: 'Dr. R. K. Mohapatra (Master Timetable & Operations)' },
  club: { username: 'club', email: 'club@cit.edu', pass: 'Club@123', title: 'Student Club Lead', subtitle: 'Vikram Seth (Spectra 2026 Fest & Venue Bookings)' },
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

  const login = async (usernameOrEmail: string, password: string, role?: string): Promise<User> => {
    setLoading(true);
    try {
      const res = await api.login(usernameOrEmail, password, role);
      setUser(res.user);
      setToken(res.access_token);
      return res.user;
    } finally {
      setLoading(false);
    }
  };

  const demoLogin = async (role: UserRole): Promise<User> => {
    const creds = DEMO_CREDENTIALS[role];
    if (creds) {
      return await login(creds.username, creds.pass, role);
    }
    throw new Error('Invalid demo role');
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
