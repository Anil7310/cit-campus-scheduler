import React, { useState } from 'react';
import { Menu, Sun, Moon, LogIn, Shield, GraduationCap, Calendar, Users } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { LoginModal } from './LoginModal';

interface NavbarProps {
  onMenuClick: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onMenuClick }) => {
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);

  let RoleIcon = Shield;
  let roleColor = 'text-rose-500';
  if (user?.role === 'coordinator') {
    RoleIcon = Calendar;
    roleColor = 'text-indigo-500';
  } else if (user?.role === 'faculty') {
    RoleIcon = GraduationCap;
    roleColor = 'text-emerald-500';
  } else if (user?.role === 'club') {
    RoleIcon = Users;
    roleColor = 'text-amber-500';
  }

  return (
    <>
      <header className="sticky top-0 z-30 h-16 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 px-4 sm:px-6 flex items-center justify-between">
        {/* Left: Mobile Toggle & Campus Badge */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center space-x-2.5">
            <img
              src="/logo.jpg"
              alt="CIT Logo"
              className="w-8 h-8 rounded-full object-cover shadow-sm ring-1 ring-slate-200 dark:ring-slate-700 bg-white"
            />
            <div className="hidden sm:flex flex-col">
              <span className="text-xs font-black tracking-tight text-slate-900 dark:text-white leading-none">
                Chilika Institute of Technology
              </span>
              <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold mt-0.5 flex items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse" />
                Spring 2026 Active
              </span>
            </div>
          </div>
        </div>

        {/* Right: Single Login / Switch Portal Option & Theme Toggle */}
        <div className="flex items-center space-x-3">
          {user ? (
            <div className="flex items-center space-x-2">
              <div className="hidden md:flex items-center space-x-1.5 px-3 py-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 text-xs">
                <RoleIcon className={`w-3.5 h-3.5 ${roleColor}`} />
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {user.name.split(' ')[0]}
                </span>
                <span className="text-[10px] font-bold uppercase text-slate-400">
                  ({user.role}{user.department ? ` • ${user.department}` : ''})
                </span>
              </div>

              <button
                onClick={() => setShowLoginModal(true)}
                className="px-3.5 py-1.5 rounded-xl bg-brand-50 dark:bg-brand-950/60 hover:bg-brand-100 dark:hover:bg-brand-900 border border-brand-200 dark:border-brand-800 text-brand-700 dark:text-brand-300 text-xs font-bold flex items-center space-x-1.5 transition-all shadow-sm"
                title="Open login and account switcher for all sections"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Login / Switch Portal</span>
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowLoginModal(true)}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white text-xs font-bold shadow-md shadow-brand-500/20 flex items-center space-x-2 transition-all"
            >
              <LogIn className="w-4 h-4" />
              <span>Login / Institutional Access</span>
            </button>
          )}

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Toggle theme"
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-slate-600" />
            )}
          </button>
        </div>
      </header>

      {/* Unified Login Modal showing all sections */}
      <LoginModal isOpen={showLoginModal} onClose={() => setShowLoginModal(false)} />
    </>
  );
};
