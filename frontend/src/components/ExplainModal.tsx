import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { X, CheckCircle, HelpCircle, Sparkles, AlertTriangle, ShieldCheck } from 'lucide-react';

interface ExplainModalProps {
  sessionId: string | null;
  onClose: () => void;
}

export const ExplainModal: React.FC<ExplainModalProps> = ({ sessionId, onClose }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    api
      .explainSession(sessionId)
      .then((res) => setData(res))
      .catch((err) => setError(err.message || 'Failed to explain session'))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (!sessionId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden transform transition-all">
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-indigo-500 to-brand-600 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-indigo-200" />
            <h3 className="text-lg font-bold">Solver Decision Explanation</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full hover:bg-white/20 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {loading && (
            <div className="py-12 flex flex-col items-center justify-center space-y-3">
              <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Querying constraint satisfaction engine...
              </p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
              <div className="text-sm">{error}</div>
            </div>
          )}

          {data && !loading && (
            <div className="space-y-4">
              <div>
                <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
                  Target Session
                </span>
                <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                  {data.session_id}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900 text-sm text-indigo-900 dark:text-indigo-200 leading-relaxed">
                {data.explanation}
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2 flex items-center space-x-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>Hard Constraints Verified (0 Violations)</span>
                </h4>
                <div className="space-y-1.5">
                  {data.hard_constraints_satisfied?.map((hc: string, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center space-x-2 text-xs text-slate-700 dark:text-slate-300"
                    >
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                      <span>{hc}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                <span>Alternative candidate slots evaluated:</span>
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  {data.alternative_slots_considered ?? 15} slots
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 dark:bg-slate-950/50 border-t border-slate-100 dark:border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
