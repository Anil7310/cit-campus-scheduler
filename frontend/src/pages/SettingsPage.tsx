import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  Settings,
  ShieldAlert,
  Sliders,
  History,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Lock
} from 'lucide-react';

interface AuditLog {
  id: string;
  action: string;
  user: string;
  details: string;
  timestamp: string;
}

export const SettingsPage: React.FC = () => {
  const [spreadWeight, setSpreadWeight] = useState(40);
  const [loadWeight, setLoadWeight] = useState(30);
  const [morningWeight, setMorningWeight] = useState(20);
  const [gapWeight, setGapWeight] = useState(10);

  const [logs, setLogs] = useState<AuditLog[]>([
    {
      id: 'LOG-001',
      action: 'GATE_A_SOLVER_PASS',
      user: 'admin@cit.edu',
      details: 'Baseline schedule solved (189 sessions, 0 hard violations)',
      timestamp: 'Today, 14:15',
    },
    {
      id: 'LOG-002',
      action: 'GATE_B_EXAMS_ALLOCATED',
      user: 'admin@cit.edu',
      details: '41 midsem exams scheduled with 50% halved room capacity',
      timestamp: 'Today, 14:32',
    },
    {
      id: 'LOG-003',
      action: 'GATE_C_DISRUPTION_REPAIR',
      user: 'coordinator@cit.edu',
      details: 'Minimal perturbation repair applied: 4 sessions moved, 0 violations',
      timestamp: 'Today, 14:48',
    },
    {
      id: 'LOG-004',
      action: 'SPECTRA_BOOKING_APPROVED',
      user: 'coordinator@cit.edu',
      details: 'REQ_01 (Robotics Workshop) allocated LH-1',
      timestamp: 'Today, 15:02',
    },
  ]);

  // Reset Modal
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetInput, setResetInput] = useState('');
  const [resetting, setResetting] = useState(false);
  const [resetSuccess, setResetSuccess] = useState<string | null>(null);

  const handleResetConfirm = async () => {
    if (resetInput !== 'RESET') return;
    setResetting(true);
    try {
      await api.resetDemoData();
      setResetSuccess('Demo dataset successfully restored to pristine Gate A/B/C state!');
      setShowResetModal(false);
      setResetInput('');
    } catch (e: any) {
      console.error(e);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      {/* Title */}
      <div>
        <div className="flex items-center space-x-2">
          <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
            System Settings & Governance
          </h1>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
            Administrative Console
          </span>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Tune soft optimization weights, review immutable audit logs, and maintain system state.
        </p>
      </div>

      {resetSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span className="font-semibold">{resetSuccess}</span>
        </div>
      )}

      {/* Solver Soft Objective Tuning */}
      <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 dark:border-slate-800 pb-3">
          <Sliders className="w-4 h-4 text-brand-500" />
          <h2 className="text-sm font-bold text-slate-900 dark:text-white">
            Soft Optimization Penalty Weights
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <div className="flex justify-between mb-1">
              <span className="font-semibold text-slate-600 dark:text-slate-400">
                Faculty Day-Spread Priority
              </span>
              <span className="font-bold text-brand-600 dark:text-brand-400">{spreadWeight}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={spreadWeight}
              onChange={(e) => setSpreadWeight(Number(e.target.value))}
              className="w-full accent-brand-600"
            />
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <span className="font-semibold text-slate-600 dark:text-slate-400">
                Max Daily Load Cap
              </span>
              <span className="font-bold text-brand-600 dark:text-brand-400">{loadWeight}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={loadWeight}
              onChange={(e) => setLoadWeight(Number(e.target.value))}
              className="w-full accent-brand-600"
            />
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <span className="font-semibold text-slate-600 dark:text-slate-400">
                Morning Hours Core Lecture Weight
              </span>
              <span className="font-bold text-brand-600 dark:text-brand-400">{morningWeight}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={morningWeight}
              onChange={(e) => setMorningWeight(Number(e.target.value))}
              className="w-full accent-brand-600"
            />
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <span className="font-semibold text-slate-600 dark:text-slate-400">
                Student Gap Minimization
              </span>
              <span className="font-bold text-brand-600 dark:text-brand-400">{gapWeight}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={gapWeight}
              onChange={(e) => setGapWeight(Number(e.target.value))}
              className="w-full accent-brand-600"
            />
          </div>
        </div>
      </div>

      {/* Immutable Audit Trail */}
      <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <History className="w-4 h-4 text-emerald-500" />
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              Institutional Audit Trail (Tamper-Resistant)
            </h2>
          </div>
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Live Stream
          </span>
        </div>

        <div className="space-y-2">
          {logs.map((log) => (
            <div
              key={log.id}
              className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2"
            >
              <div>
                <span className="font-bold text-slate-800 dark:text-slate-200">
                  {log.action}
                </span>
                <span className="text-slate-400 ml-2">by {log.user}</span>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  {log.details}
                </p>
              </div>
              <span className="text-[10px] text-slate-400 shrink-0">{log.timestamp}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Danger Zone: Reset Demo Data */}
      <div className="p-6 rounded-3xl bg-rose-500/5 dark:bg-rose-950/20 border border-rose-500/20 space-y-3">
        <div className="flex items-center space-x-2 text-rose-600 dark:text-rose-400">
          <ShieldAlert className="w-4 h-4" />
          <h2 className="text-sm font-bold">System Maintenance Zone</h2>
        </div>
        <p className="text-xs text-rose-700/80 dark:text-rose-300/80">
          Reset all modified sessions, approved bookings, and disruption overrides back to the pristine benchmark datasets (passing Gates A, B, and C).
        </p>

        <button
          onClick={() => setShowResetModal(true)}
          className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-colors flex items-center space-x-1.5 shadow-sm"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Demo Data</span>
        </button>
      </div>

      {/* Reset Confirmation Modal */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center space-x-2 text-rose-600">
              <AlertTriangle className="w-5 h-5" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Confirm Database Reset
              </h3>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              This action will purge all runtime modifications and restore the clean benchmark data. Type <strong className="text-rose-600">RESET</strong> to confirm.
            </p>
            <input
              type="text"
              value={resetInput}
              onChange={(e) => setResetInput(e.target.value)}
              placeholder="Type RESET here"
              className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-bold text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-rose-500"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowResetModal(false);
                  setResetInput('');
                }}
                className="px-3 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={handleResetConfirm}
                disabled={resetInput !== 'RESET' || resetting}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-600 text-white hover:bg-rose-700 disabled:opacity-40 transition-colors"
              >
                {resetting ? 'Resetting...' : 'Permanently Reset'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
