import React from 'react';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';
import { Shield, GraduationCap, Users, Calendar, LogOut } from 'lucide-react';

export const DemoSwitcher: React.FC = () => {
  const { user, demoLogin, logout } = useAuth();

  const roles: { role: UserRole; label: string; icon: any; color: string }[] = [
    { role: 'admin', label: 'Admin', icon: Shield, color: 'text-rose-500 hover:border-rose-500' },
    { role: 'coordinator', label: 'Coordinator', icon: Calendar, color: 'text-indigo-500 hover:border-indigo-500' },
    { role: 'faculty', label: 'Faculty', icon: GraduationCap, color: 'text-emerald-500 hover:border-emerald-500' },
    { role: 'club', label: 'Club Lead', icon: Users, color: 'text-amber-500 hover:border-amber-500' },
  ];

  return (
    <div className="flex items-center space-x-1.5 p-1 bg-slate-100 dark:bg-slate-800/80 rounded-xl border border-slate-200/80 dark:border-slate-700/60 text-xs">
      <span className="hidden lg:inline text-[10px] font-bold uppercase tracking-wider text-slate-400 px-2">
        Demo Persona:
      </span>
      {roles.map((item) => {
        const Icon = item.icon;
        const isActive = user?.role === item.role;
        return (
          <button
            key={item.role}
            onClick={() => demoLogin(item.role)}
            className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg transition-all font-medium ${
              isActive
                ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm ring-1 ring-slate-200 dark:ring-slate-600'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
            title={`Switch to ${item.label}`}
          >
            <Icon className={`w-3.5 h-3.5 ${item.color}`} />
            <span>{item.label}</span>
          </button>
        );
      })}

      {user && (
        <button
          onClick={logout}
          className="ml-1 p-1 text-slate-400 hover:text-rose-500 rounded-lg transition-colors"
          title="Sign Out"
        >
          <LogOut className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};
