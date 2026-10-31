import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';
import {
  Shield,
  GraduationCap,
  Users,
  Calendar,
  Lock,
  Mail,
  ArrowRight,
  Sparkles,
  AlertCircle
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, demoLogin } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async (role: UserRole) => {
    setError(null);
    setLoading(true);
    try {
      await demoLogin(role);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen -m-4 sm:-m-6 lg:-m-8 flex flex-col justify-center items-center p-4 bg-slate-50 dark:bg-slate-950">
      <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 bg-white dark:bg-slate-900 rounded-3xl shadow-2xl border border-slate-200/80 dark:border-slate-800 overflow-hidden">
        
        {/* Left Side: Brand & One-Click Demo Access */}
        <div className="p-8 sm:p-10 bg-gradient-to-br from-indigo-600 via-brand-600 to-indigo-900 text-white flex flex-col justify-between">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-xs font-semibold tracking-wide text-indigo-100 mb-6">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              <span>Chilika Institute of Technology</span>
            </div>
            
            <h1 className="text-3xl font-extrabold tracking-tight mb-3">
              Campus Scheduling & Venue Engine
            </h1>
            <p className="text-sm text-indigo-100/90 leading-relaxed mb-8">
              OR-Tools CP-SAT powered timetable clash-prevention, 50% capacity midsem exams, and dynamic rescheduling for 14 groups & 40 faculty.
            </p>

            {/* Quick Demo Personas */}
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-wider text-indigo-200">
                Instant One-Click Demo Access
              </p>

              <button
                onClick={() => handleDemo('admin')}
                disabled={loading}
                className="w-full p-3 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 flex items-center justify-between text-left transition-all"
              >
                <div className="flex items-center space-x-3">
                  <Shield className="w-5 h-5 text-rose-300" />
                  <div>
                    <div className="text-xs font-bold">System Administrator</div>
                    <div className="text-[11px] text-indigo-200">admin@cit.edu (Full permissions)</div>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-indigo-200" />
              </button>

              <button
                onClick={() => handleDemo('coordinator')}
                disabled={loading}
                className="w-full p-3 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 flex items-center justify-between text-left transition-all"
              >
                <div className="flex items-center space-x-3">
                  <Calendar className="w-5 h-5 text-indigo-200" />
                  <div>
                    <div className="text-xs font-bold">Academic Coordinator</div>
                    <div className="text-[11px] text-indigo-200">coordinator@cit.edu (Approve & Disruption)</div>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-indigo-200" />
              </button>

              <button
                onClick={() => handleDemo('faculty')}
                disabled={loading}
                className="w-full p-3 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 flex items-center justify-between text-left transition-all"
              >
                <div className="flex items-center space-x-3">
                  <GraduationCap className="w-5 h-5 text-emerald-300" />
                  <div>
                    <div className="text-xs font-bold">Faculty Member</div>
                    <div className="text-[11px] text-indigo-200">faculty@cit.edu (View & Book)</div>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-indigo-200" />
              </button>

              <button
                onClick={() => handleDemo('club')}
                disabled={loading}
                className="w-full p-3 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 flex items-center justify-between text-left transition-all"
              >
                <div className="flex items-center space-x-3">
                  <Users className="w-5 h-5 text-amber-300" />
                  <div>
                    <div className="text-xs font-bold">Student Club Lead</div>
                    <div className="text-[11px] text-indigo-200">club@cit.edu (Spectra bookings)</div>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-indigo-200" />
              </button>
            </div>
          </div>

          <div className="pt-6 text-[11px] text-indigo-200/70 border-t border-white/10">
            CIT Engine v2.4 • 0 Hard Violations Guaranteed
          </div>
        </div>

        {/* Right Side: Manual Form */}
        <div className="p-8 sm:p-10 flex flex-col justify-center bg-white dark:bg-slate-900">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Sign In</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Authenticate with your institutional CIT credentials
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleManualLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Institutional Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@cit.edu"
                  required
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs focus:ring-2 focus:ring-brand-500 outline-none transition-all"
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
                  placeholder="••••••••"
                  required
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs focus:ring-2 focus:ring-brand-500 outline-none transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs transition-colors shadow-lg shadow-brand-500/25 flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800 text-center">
            <span className="text-[11px] text-slate-400">
              Chilika Institute of Technology • Timetable & Exam Committee
            </span>
          </div>
        </div>

      </div>
    </div>
  );
};
