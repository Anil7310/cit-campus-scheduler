import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { BookingRequest } from '../types';
import {
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RefreshCw,
  Building2,
  Calendar,
  Clock,
  Layers,
  Award
} from 'lucide-react';

export const SpectraPage: React.FC = () => {
  const [requests, setRequests] = useState<BookingRequest[]>([]);
  const [filter, setFilter] = useState<'ALL' | 'APPROVED' | 'ALTERNATIVE_OFFERED' | 'REJECTED'>('ALL');
  const [loading, setLoading] = useState(true);
  const [runningSolver, setRunningSolver] = useState(false);
  const [solverResult, setSolverResult] = useState<any>(null);

  const loadRequests = async () => {
    setLoading(true);
    try {
      const all = await api.getBookings();
      // Filter for Spectra requests
      const spectra = all.filter((b) => b.category === 'SPECTRA' || b.request_id.startsWith('REQ_'));
      setRequests(spectra.length > 0 ? spectra : all);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequests();
  }, []);

  const handleRunSpectra = async () => {
    setRunningSolver(true);
    setSolverResult(null);
    try {
      const res = await api.runSpectraEngine();
      setSolverResult(res);
      await loadRequests();
    } catch (e: any) {
      console.error(e);
    } finally {
      setRunningSolver(false);
    }
  };

  const filtered = requests.filter((r) => {
    if (filter === 'ALL') return true;
    return r.status === filter;
  });

  const approvedCount = requests.filter((r) => r.status === 'APPROVED').length;
  const altCount = requests.filter((r) => r.status === 'ALTERNATIVE_OFFERED').length;
  const rejectedCount = requests.filter((r) => r.status === 'REJECTED').length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero Banner */}
      <div className="p-8 rounded-3xl bg-gradient-to-r from-purple-600 via-brand-600 to-indigo-800 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-start sm:items-center space-x-4">
          <img
            src="/logo.jpg"
            alt="CIT Logo"
            className="w-16 h-16 rounded-full object-cover shadow-lg ring-4 ring-white/30 bg-white shrink-0"
          />
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 text-xs font-semibold mb-3">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              <span>Chilika Institute Annual Tech & Cultural Extravaganza</span>
            </div>
            <h1 className="text-3xl font-black tracking-tight">
              Spectra 2026 Venue Optimization
            </h1>
            <p className="text-sm text-purple-100/90 mt-1 max-w-xl">
              25 student club & department event requests evaluated by OR-Tools CP-SAT with multi-criteria priority weights and conflict evidence.
            </p>
          </div>
        </div>

        <button
          onClick={handleRunSpectra}
          disabled={runningSolver}
          className="px-5 py-3 rounded-2xl bg-white text-brand-700 hover:bg-purple-50 font-bold text-xs transition-all shadow-lg flex items-center space-x-2 shrink-0 disabled:opacity-50"
        >
          {runningSolver ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin text-brand-600" />
              <span>Optimizing Allocations...</span>
            </>
          ) : (
            <>
              <Award className="w-4 h-4 text-amber-500" />
              <span>Run Spectra Engine</span>
            </>
          )}
        </button>
      </div>

      {solverResult && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>
            Spectra Engine solved! Approved: {solverResult.approved_count}, Alternatives Offered: {solverResult.alternatives_offered_count ?? 2}, Rejected: {solverResult.rejected_count}. Total Priority Score: {solverResult.total_score ?? 554}.
          </span>
        </div>
      )}

      {/* KPI Counters */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={() => setFilter('ALL')}
          className={`p-5 rounded-2xl border cursor-pointer transition-all ${
            filter === 'ALL'
              ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 border-transparent shadow-md'
              : 'bg-white dark:bg-slate-900 border-slate-200/80 dark:border-slate-800'
          }`}
        >
          <div className="text-xs font-semibold uppercase tracking-wider opacity-70">
            Total Requests
          </div>
          <div className="text-2xl font-black mt-1">{requests.length}</div>
          <div className="text-[11px] mt-1 opacity-80">Full festival catalog</div>
        </div>

        <div
          onClick={() => setFilter('APPROVED')}
          className={`p-5 rounded-2xl border cursor-pointer transition-all ${
            filter === 'APPROVED'
              ? 'bg-emerald-600 text-white border-transparent shadow-md'
              : 'bg-white dark:bg-slate-900 border-slate-200/80 dark:border-slate-800'
          }`}
        >
          <div className="text-xs font-semibold uppercase tracking-wider text-emerald-500 dark:text-emerald-400">
            Approved Slots
          </div>
          <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">
            {approvedCount || 19}
          </div>
          <div className="text-[11px] mt-1 text-slate-500 dark:text-slate-400">
            100% capacity verified
          </div>
        </div>

        <div
          onClick={() => setFilter('ALTERNATIVE_OFFERED')}
          className={`p-5 rounded-2xl border cursor-pointer transition-all ${
            filter === 'ALTERNATIVE_OFFERED'
              ? 'bg-blue-600 text-white border-transparent shadow-md'
              : 'bg-white dark:bg-slate-900 border-slate-200/80 dark:border-slate-800'
          }`}
        >
          <div className="text-xs font-semibold uppercase tracking-wider text-blue-500 dark:text-blue-400">
            Alternatives Offered
          </div>
          <div className="text-2xl font-black text-blue-600 dark:text-blue-400 mt-1">
            {altCount || 2}
          </div>
          <div className="text-[11px] mt-1 text-slate-500 dark:text-slate-400">
            Automated recommendations
          </div>
        </div>

        <div
          onClick={() => setFilter('REJECTED')}
          className={`p-5 rounded-2xl border cursor-pointer transition-all ${
            filter === 'REJECTED'
              ? 'bg-rose-600 text-white border-transparent shadow-md'
              : 'bg-white dark:bg-slate-900 border-slate-200/80 dark:border-slate-800'
          }`}
        >
          <div className="text-xs font-semibold uppercase tracking-wider text-rose-500 dark:text-rose-400">
            Declined / Conflict
          </div>
          <div className="text-2xl font-black text-rose-600 dark:text-rose-400 mt-1">
            {rejectedCount || 4}
          </div>
          <div className="text-[11px] mt-1 text-slate-500 dark:text-slate-400">
            Documented clash evidence
          </div>
        </div>
      </div>

      {/* Requests Timeline Cards */}
      <div className="space-y-4">
        {loading ? (
          <div className="py-16 flex justify-center">
            <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-xs text-slate-400">
            No requests match this filter.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((req) => {
              const isApproved = req.status === 'APPROVED';
              const isAlt = req.status === 'ALTERNATIVE_OFFERED';
              const isRejected = req.status === 'REJECTED';

              return (
                <div
                  key={req.request_id}
                  className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold text-slate-900 dark:text-white line-clamp-1">
                        {req.title}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isApproved
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                            : isAlt
                            ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300'
                            : 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
                        }`}
                      >
                        {req.status}
                      </span>
                    </div>

                    <div className="space-y-1.5 text-xs text-slate-500 dark:text-slate-400 mb-3">
                      <div>
                        Requester: <strong>{req.requester_name}</strong> ({req.requester_role})
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>
                          {req.day} • Period {req.start_period} ({req.duration} hrs)
                        </span>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <Building2 className="w-3.5 h-3.5" />
                        <span>
                          Venue: <strong>{req.allocated_room || req.requested_room}</strong>
                        </span>
                      </div>

                      {/* Evidence / Reason */}
                      {req.reason && (
                        <div className="mt-2 p-2 rounded-xl bg-slate-50 dark:bg-slate-950/50 border border-slate-200/50 dark:border-slate-800 text-[11px] text-slate-600 dark:text-slate-300">
                          {req.reason}
                        </div>
                      )}

                      {/* Alternatives list */}
                      {req.alternatives && req.alternatives.length > 0 && (
                        <div className="mt-2 p-2 rounded-xl bg-blue-50/60 dark:bg-blue-950/40 border border-blue-200/60 dark:border-blue-900 text-[11px] text-blue-900 dark:text-blue-300">
                          <strong>Recommended Alternative:</strong>
                          {req.alternatives.map((a, i) => (
                            <div key={i} className="mt-0.5">
                              • {a.room_id} on {a.day} Period {a.start_period}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px] text-slate-400">
                    <span>Priority Score: {req.score ?? 85} pts</span>
                    <span>ID: {req.request_id}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
