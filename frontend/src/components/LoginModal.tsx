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
  X,
  LogOut,
  Building
} from 'lucide-react';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface RoleConfig {
  role: UserRole;
  title: string;
  badge: string;
  department: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  accentColor: string;
  bgGradient: string;
  borderColor: string;
  defaultUsername: string;
  landingPage: string;
}

const ROLES: RoleConfig[] = [
  {
    role: 'admin',
    title: 'System Administrator',
    badge: "Dean's Office",
    department: "Dean's Office",
    description: 'Master administrative control, member creation, curriculum catalog, and institutional approvals hub.',
    icon: Shield,
    accentColor: 'text-rose-500',
    bgGradient: 'from-rose-500/10 to-indigo-500/10',
    borderColor: 'border-rose-500/30 hover:border-rose-500',
    defaultUsername: 'admin',
    landingPage: '/'
  },
  {
    role: 'coordinator',
    title: 'Academic Coordinator',
    badge: 'Department HOD / Registrar',
    department: 'CSE / Assigned Dept',
    description: 'Access restricted strictly to respective department curriculum, sessions & timetable. Department modifications require Admin approval.',
    icon: Calendar,
    accentColor: 'text-indigo-500',
    bgGradient: 'from-indigo-500/10 to-blue-500/10',
    borderColor: 'border-indigo-500/30 hover:border-indigo-500',
    defaultUsername: 'coordinator',
    landingPage: '/'
  },
  {
    role: 'faculty',
    title: 'Teaching Faculty',
    badge: 'Faculty Member',
    department: 'CSE / Respective Dept',
    description: 'Personal day-by-day timetable, lecture cancel/reschedule with student batch vacancy matching, and weekend extra classes.',
    icon: GraduationCap,
    accentColor: 'text-emerald-500',
    bgGradient: 'from-emerald-500/10 to-teal-500/10',
    borderColor: 'border-emerald-500/30 hover:border-emerald-500',
    defaultUsername: 'faculty',
    landingPage: '/faculty'
  },
  {
    role: 'club',
    title: 'Student Club Lead',
    badge: 'Spectra & Societies',
    department: 'Student Council',
    description: 'Instant venue bookings, real-time clash verification, and Spectra 2026 fest event scheduling.',
    icon: Users,
    accentColor: 'text-amber-500',
    bgGradient: 'from-amber-500/10 to-orange-500/10',
    borderColor: 'border-amber-500/30 hover:border-amber-500',
    defaultUsername: 'club',
    landingPage: '/spectra'
  }
];

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose }) => {
  const { user, login, demoLogin, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<UserRole>('faculty');
  const [manualUsername, setManualUsername] = useState('faculty');
  const [manualPassword, setManualPassword] = useState('Faculty@123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSelectRole = (role: UserRole) => {
    setActiveTab(role);
    setError(null);
    setSuccessMsg(null);
    const cred = DEMO_CREDENTIALS[role];
    if (cred) {
      setManualUsername(cred.username);
      setManualPassword(cred.pass);
    }
  };

  const handleDemoLogin = async (role: UserRole) => {
    setLoading(true);
    setError(null);
    try {
      await demoLogin(role);
      const conf = ROLES.find((r) => r.role === role);
      setSuccessMsg(`Logged in as ${conf?.title}! Redirecting...`);
      setTimeout(() => {
        onClose();
        if (conf?.landingPage) {
          navigate(conf.landingPage);
        }
      }, 500);
    } catch (err: any) {
      setError(err.message || 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualUsername.trim() || !manualPassword.trim()) {
      setError('Please enter both username and password.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await login(manualUsername.trim(), manualPassword.trim(), activeTab);
      const conf = ROLES.find((r) => r.role === activeTab);
      setSuccessMsg(`Logged in successfully!`);
      setTimeout(() => {
        onClose();
        if (conf?.landingPage) {
          navigate(conf.landingPage);
        }
      }, 500);
    } catch (err: any) {
      setError(err.message || 'Invalid username or password for this role.');
    } finally {
      setLoading(false);
    }
  };

  const activeConfig = ROLES.find((r) => r.role === activeTab) || ROLES[0];
  const ActiveIcon = activeConfig.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-4xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/60 dark:bg-slate-800/40">
          <div className="flex items-center space-x-3.5">
            <img
              src="/logo.jpg"
              alt="CIT Logo"
              className="w-11 h-11 rounded-full object-cover shadow-md ring-2 ring-brand-500/30 bg-white shrink-0"
            />
            <div>
              <h2 className="text-lg font-black tracking-tight text-slate-900 dark:text-white flex items-center space-x-2">
                <span>CIT Institutional Login & Portal Access</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-brand-100 text-brand-800 dark:bg-brand-950/60 dark:text-brand-300">
                  Role-Based
                </span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Choose your institutional section to sign in or use one-click demo login
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {user && (
              <button
                onClick={() => {
                  logout();
                  setSuccessMsg('Signed out successfully.');
                }}
                className="px-3 py-1.5 rounded-xl border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400 text-xs font-semibold hover:bg-rose-50 dark:hover:bg-rose-950/50 flex items-center space-x-1.5 transition-all"
                title="Sign out current session"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out ({user.name.split(' ')[0]})</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body: 4 Sections Selector */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Section Selection Cards */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2.5">
              1. Select Institutional Section:
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {ROLES.map((r) => {
                const Icon = r.icon;
                const isSelected = activeTab === r.role;
                const isCurrent = user?.role === r.role;

                return (
                  <button
                    key={r.role}
                    type="button"
                    onClick={() => handleSelectRole(r.role)}
                    className={`p-4 rounded-2xl border text-left transition-all relative flex flex-col justify-between ${
                      isSelected
                        ? `bg-slate-50 dark:bg-slate-800/80 ${r.borderColor} ring-2 ring-brand-500/20 shadow-md`
                        : 'bg-white dark:bg-slate-900 border-slate-200/80 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className={`p-2 rounded-xl bg-slate-100 dark:bg-slate-800 ${r.accentColor}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        {isCurrent && (
                          <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
                            Active
                          </span>
                        )}
                      </div>
                      <h3 className="text-xs font-bold text-slate-900 dark:text-white">
                        {r.title}
                      </h3>
                      <p className="text-[10px] text-slate-400 mt-0.5 font-medium">
                        {r.badge}
                      </p>
                    </div>

                    <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] font-semibold text-brand-600 dark:text-brand-400">
                      <span>{isSelected ? 'Selected' : 'Choose'}</span>
                      <ArrowRight className="w-3 h-3" />
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Section Details & Login Options */}
          <div className="p-6 rounded-2xl bg-slate-50/80 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-700/60 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/60 dark:border-slate-700/60">
              <div className="flex items-center space-x-3">
                <div className={`p-2.5 rounded-xl bg-white dark:bg-slate-900 shadow-sm ${activeConfig.accentColor}`}>
                  <ActiveIcon className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-black text-slate-900 dark:text-white">
                      {activeConfig.title} Section
                    </h3>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                      {activeConfig.badge}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {activeConfig.description}
                  </p>
                </div>
              </div>

              {/* Instant One-Click Demo Login Button */}
              <button
                type="button"
                onClick={() => handleDemoLogin(activeTab)}
                disabled={loading}
                className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-extrabold text-xs shadow-md shadow-amber-500/20 flex items-center justify-center space-x-2 transition-all shrink-0 disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                <span>⚡ 1-Click Demo Login as {activeConfig.badge.split(' ')[0]}</span>
              </button>
            </div>

            {/* Error & Success Messages */}
            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            {successMsg && (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}

            {/* Manual Credentials Form */}
            <form onSubmit={handleManualLogin} className="space-y-3 pt-1">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 font-semibold">
                <span>Or sign in with assigned credentials:</span>
                <span className="text-[11px] text-slate-400">
                  Demo User: <code className="text-brand-600 dark:text-brand-400 font-bold">{activeConfig.defaultUsername}</code>
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Username / Institutional ID
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                    <input
                      type="text"
                      required
                      value={manualUsername}
                      onChange={(e) => setManualUsername(e.target.value)}
                      placeholder="Username"
                      className="w-full text-xs pl-9 pr-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 outline-none focus:ring-2 focus:ring-brand-500/30"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                    <input
                      type="password"
                      required
                      value={manualPassword}
                      onChange={(e) => setManualPassword(e.target.value)}
                      placeholder="Password"
                      className="w-full text-xs pl-9 pr-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 outline-none focus:ring-2 focus:ring-brand-500/30"
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-[11px] text-slate-400">
                  Landing Portal: <strong className="text-slate-700 dark:text-slate-300">{activeConfig.landingPage}</strong>
                </span>

                <button
                  type="submit"
                  disabled={loading}
                  className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-md shadow-brand-500/20 flex items-center space-x-1.5 transition-all disabled:opacity-50"
                >
                  {loading ? (
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <ArrowRight className="w-3.5 h-3.5" />
                  )}
                  <span>Sign In as {activeConfig.badge.split(' ')[0]}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

