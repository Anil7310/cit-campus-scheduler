import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, DEMO_CREDENTIALS } from '../context/AuthContext';
import { UserRole } from '../types';
import {
  Shield,
  GraduationCap,
  Users,
  Calendar,
  Lock,
  User,
  ArrowRight,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  KeyRound,
  Compass
} from 'lucide-react';

interface RoleCardConfig {
  role: UserRole;
  title: string;
  badge: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  accentColor: string;
  defaultUsername: string;
  landingPage: string;
}

const ROLE_OPTIONS: RoleCardConfig[] = [
  {
    role: 'admin',
    title: 'System Administrator',
    badge: 'Dean\'s Office',
    description: 'Master system controls, course catalog, solver configuration, audit trail & member account creation.',
    icon: Shield,
    accentColor: 'from-rose-500 to-indigo-600',
    defaultUsername: 'admin',
    landingPage: '/'
  },
  {
    role: 'faculty',
    title: 'Faculty Member',
    badge: 'Teaching Faculty',
    description: 'Personal day-by-day timetable, lecture cancel/reschedule with student batch vacancy matching & weekend requests.',
    icon: GraduationCap,
    accentColor: 'from-emerald-500 to-teal-600',
    defaultUsername: 'faculty',
    landingPage: '/faculty'
  },
  {
    role: 'coordinator',
    title: 'Academic Coordinator',
    badge: 'Department Council',
    description: 'Master campus timetable, venue conflict arbitration, disruption solver & midsem exam allocations.',
    icon: Calendar,
    accentColor: 'from-indigo-500 to-blue-600',
    defaultUsername: 'coordinator',
    landingPage: '/'
  },
  {
    role: 'club',
    title: 'Student Club Lead',
    badge: 'Spectra & Societies',
    description: 'Instant venue bookings, Spectra 2026 fest event scheduling & room availability lookups.',
    icon: Users,
    accentColor: 'from-amber-500 to-orange-600',
    defaultUsername: 'club',
    landingPage: '/spectra'
  }
];

export const LoginPage: React.FC = () => {
  const { login, demoLogin } = useAuth();
  const navigate = useNavigate();

  const [selectedRole, setSelectedRole] = useState<UserRole>('faculty');
  const [username, setUsername] = useState('faculty');
  const [password, setPassword] = useState('Faculty@123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeRoleConfig = ROLE_OPTIONS.find((r) => r.role === selectedRole) || ROLE_OPTIONS[1];

  const handleSelectRole = (role: UserRole) => {
    setSelectedRole(role);
    setError(null);
    const cred = DEMO_CREDENTIALS[role];
    if (cred) {
      setUsername(cred.username);
      setPassword(cred.pass);
    }
  };

  const handleDemoClick = async () => {
    setLoading(true);
    setError(null);
    try {
      const u = await demoLogin(selectedRole);
      if (u.role === 'faculty') navigate('/faculty');
      else if (u.role === 'club') navigate('/spectra');
      else navigate('/');
    } catch (err: any) {
      setError(err.message || 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please enter your username and password.');
      return;
    }

    setError(null);
    setLoading(true);
    try {
      const authenticatedUser = await login(username.trim(), password, selectedRole);
      
      // Navigate directly to respective portal based on user data
      if (authenticatedUser.role === 'faculty') {
        navigate('/faculty');
      } else if (authenticatedUser.role === 'club') {
        navigate('/spectra');
      } else {
        navigate('/');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen -m-4 sm:-m-6 lg:-m-8 flex flex-col justify-center items-center p-4 sm:p-6 bg-slate-50 dark:bg-slate-950">
      
      {/* Brand Header */}
      <div className="text-center max-w-xl mb-6 flex flex-col items-center">
        <img
          src="/logo.jpg"
          alt="Chilika Institute of Technology Logo"
          className="w-24 h-24 rounded-full object-cover shadow-lg ring-4 ring-brand-500/30 bg-white mb-4 animate-fade-in"
        />
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-600 dark:text-brand-300 text-xs font-semibold tracking-wide mb-3">
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          <span>Chilika Institute of Technology (CIT)</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Institutional Scheduling & Portal Login
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5">
          Select your institutional role below, enter your assigned username, and access your role-specific portal
        </p>
      </div>

      <div className="w-full max-w-4xl bg-white dark:bg-slate-900 rounded-3xl shadow-xl border border-slate-200/80 dark:border-slate-800 overflow-hidden">
        
        {/* Step 1: Select Login Role Option */}
        <div className="p-6 bg-slate-50/70 dark:bg-slate-900/60 border-b border-slate-200/80 dark:border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Step 1: Choose Your Portal Role
            </span>
            <span className="text-[11px] text-slate-400">
              Only authorized members can log in
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {ROLE_OPTIONS.map((opt) => {
              const Icon = opt.icon;
              const isSelected = selectedRole === opt.role;

              return (
                <button
                  key={opt.role}
                  type="button"
                  onClick={() => handleSelectRole(opt.role)}
                  className={`p-3.5 rounded-2xl border text-left transition-all relative overflow-hidden flex flex-col justify-between ${
                    isSelected
                      ? 'bg-white dark:bg-slate-800 border-brand-500 dark:border-brand-400 shadow-md ring-2 ring-brand-500/20'
                      : 'bg-white/60 dark:bg-slate-850 border-slate-200/80 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                >
                  {isSelected && (
                    <div className="absolute top-2 right-2">
                      <CheckCircle2 className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                    </div>
                  )}
                  <div className={`w-9 h-9 rounded-xl bg-gradient-to-tr ${opt.accentColor} flex items-center justify-center text-white mb-2 shadow-sm`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-900 dark:text-white">
                      {opt.title}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5 font-medium">
                      {opt.badge}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Step 2: Form & Role Details */}
        <div className="grid grid-cols-1 md:grid-cols-5 p-6 sm:p-8 gap-8 items-center">
          
          {/* Left explanation of selected portal */}
          <div className="md:col-span-2 space-y-4 border-b md:border-b-0 md:border-r border-slate-100 dark:border-slate-800 md:pr-6">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-1 rounded-lg bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-300 font-bold text-xs border border-brand-200 dark:border-brand-800 uppercase">
                {activeRoleConfig.title}
              </span>
            </div>

            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Accessing {activeRoleConfig.title}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              {activeRoleConfig.description}
            </p>

            <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-700/60 text-[11px] text-slate-600 dark:text-slate-300 space-y-1">
              <div className="font-semibold text-slate-900 dark:text-white flex items-center space-x-1">
                <KeyRound className="w-3.5 h-3.5 text-brand-500" />
                <span>Default Demo Username:</span>
              </div>
              <p>Username: <strong className="text-brand-600 dark:text-brand-400 font-mono">{activeRoleConfig.defaultUsername}</strong></p>
              <p className="text-slate-400 text-[10px]">Or enter any username created by the Administrator</p>
            </div>
          </div>

          {/* Right: Username & Password Inputs */}
          <div className="md:col-span-3">
            <div className="mb-4">
              <h4 className="text-base font-bold text-slate-900 dark:text-white">
                Enter Credentials
              </h4>
              <p className="text-xs text-slate-400">
                Log in with your username assigned by the CIT Administrator
              </p>
            </div>

            {error && (
              <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Username or Institutional Email
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. faculty, admin, or prof_das"
                    required
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none transition-all font-medium"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    required
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none transition-all"
                  />
                </div>
              </div>

              <div className="pt-2 space-y-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-bold text-xs transition-all shadow-md shadow-brand-500/25 flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  {loading ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <span>Sign In & Open {activeRoleConfig.title} Portal</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleDemoClick}
                  disabled={loading}
                  className="w-full py-2.5 px-4 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-700 dark:text-amber-300 font-extrabold text-xs transition-all flex items-center justify-center space-x-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  <span>⚡ Instant 1-Click Demo Login as {activeRoleConfig.title}</span>
                </button>
              </div>
            </form>

            <div className="mt-4 flex items-center justify-between text-[11px] text-slate-400">
              <span>Admin assigns new usernames</span>
              <button
                type="button"
                onClick={() => handleSelectRole(selectedRole)}
                className="text-brand-600 dark:text-brand-400 hover:underline font-medium"
              >
                Reset Default Demo Pass
              </button>
            </div>
          </div>

        </div>

      </div>

      <div className="mt-6 text-center text-[11px] text-slate-400 flex items-center space-x-2">
        <Compass className="w-3.5 h-3.5 text-brand-500" />
        <span>Chilika Institute of Technology • Automated AI CP-SAT Scheduling Engine</span>
      </div>

    </div>
  );
};
