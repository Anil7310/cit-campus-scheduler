import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { TimetableSession, Room, DayOfWeek } from '../types';
import {
  Sliders,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Building2,
  Calendar,
  Clock,
  Sparkles,
  RefreshCw,
  ShieldAlert,
  SendHorizontal
} from 'lucide-react';

const DAYS: DayOfWeek[] = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
const PERIODS = [1, 2, 3, 4, 5, 6, 7, 8, 9];

export const ManualSchedulingPage: React.FC = () => {
  const { user } = useAuth();
  const isCoordinator = user?.role === 'coordinator';
  const coordDept = (user?.department || 'CSE').toUpperCase();

  const [sessions, setSessions] = useState<TimetableSession[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);

  // Selected session to move
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  const [targetDay, setTargetDay] = useState<DayOfWeek>('MON');
  const [targetPeriod, setTargetPeriod] = useState<number>(1);
  const [targetRoom, setTargetRoom] = useState<string>('CR-1');

  // Filtered sessions for coordinator
  const displaySessions = useMemo(() => {
    if (!isCoordinator) return sessions;
    return sessions.filter((s) => {
      const code = s.course_code.toUpperCase();
      const group = s.group_id.toUpperCase();
      return (
        code.startsWith(coordDept) ||
        group.includes(coordDept) ||
        (coordDept === 'CSE' && code.startsWith('CS'))
      );
    });
  }, [sessions, isCoordinator, coordDept]);

  // Validation results
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    is_valid: boolean;
    hard_violations: string[];
    soft_penalty_delta: number;
  } | null>(null);

  const [committing, setCommitting] = useState(false);
  const [commitMessage, setCommitMessage] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [sched, rList] = await Promise.all([
          api.getSchedule(),
          api.getRooms(),
        ]);
        const allSessions: TimetableSession[] = sched.sessions || [];
        setSessions(allSessions);
        setRooms(rList || []);

        const validInitial = isCoordinator
          ? allSessions.filter((s) => {
              const code = s.course_code.toUpperCase();
              const group = s.group_id.toUpperCase();
              return (
                code.startsWith(coordDept) ||
                group.includes(coordDept) ||
                (coordDept === 'CSE' && code.startsWith('CS'))
              );
            })
          : allSessions;

        if (validInitial.length > 0) {
          setSelectedSessionId(validInitial[0].session_id);
          setTargetDay(validInitial[0].day);
          setTargetPeriod(validInitial[0].start_period);
          setTargetRoom(validInitial[0].room_id);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [isCoordinator, coordDept]);

  const activeSession = sessions.find((s) => s.session_id === selectedSessionId);

  // Validate on parameter change
  useEffect(() => {
    if (!selectedSessionId || !targetRoom) return;

    const runValidation = async () => {
      setValidating(true);
      setCommitMessage(null);
      try {
        const res = await api.validateManualMove({
          session_id: selectedSessionId,
          new_day: targetDay,
          new_start_period: targetPeriod,
          new_room_id: targetRoom,
        });
        setValidationResult(res);
      } catch (e: any) {
        setValidationResult({
          is_valid: false,
          hard_violations: [e.message || 'Validation service unreachable'],
          soft_penalty_delta: 0,
        });
      } finally {
        setValidating(false);
      }
    };

    runValidation();
  }, [selectedSessionId, targetDay, targetPeriod, targetRoom]);

  const handleCommitMove = async () => {
    if (!validationResult?.is_valid) return;
    setCommitting(true);
    setCommitMessage(null);
    try {
      const res: any = await api.commitManualMove({
        session_id: selectedSessionId,
        new_day: targetDay,
        new_start_period: targetPeriod,
        new_room_id: targetRoom,
      });

      if (res.requires_admin_approval) {
        setCommitMessage(`📋 ${res.message} (Request ID: ${res.request?.request_id || 'COORD_REQ'}, Status: PENDING_ADMIN_APPROVAL)`);
      } else {
        setCommitMessage(`Session ${selectedSessionId} successfully moved and published!`);
      }

      // Refresh schedule
      const sched = await api.getSchedule();
      setSessions(sched.sessions || []);
    } catch (err: any) {
      setCommitMessage(`Move failed: ${err.message}`);
    } finally {
      setCommitting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      {/* Title */}
      <div>
        <div className="flex items-center space-x-2">
          <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
            Manual Placement & Constraint Verifier
          </h1>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-brand-100 text-brand-800 dark:bg-brand-950/60 dark:text-brand-300">
            Live Check
          </span>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Select any scheduled session and test target slots with instant validation of all hard constraints.
        </p>
      </div>

      {/* Coordinator Scope Notification */}
      {isCoordinator && (
        <div className="p-3.5 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800 flex items-center justify-between text-xs text-indigo-900 dark:text-indigo-200">
          <div className="flex items-center space-x-2 font-semibold">
            <ShieldAlert className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
            <span>🏛️ Department Coordinator View: Scoped strictly to {coordDept} sessions. Relocations will be submitted to Administrator for approval.</span>
          </div>
          <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-indigo-200/60 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-300">
            {coordDept} Department
          </span>
        </div>
      )}

      {/* Editor Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-6">
        {/* Step 1: Pick Session */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
            1. Select Session to Relocate {isCoordinator ? `(${coordDept} Department)` : ''}
          </label>
          <select
            value={selectedSessionId}
            onChange={(e) => {
              setSelectedSessionId(e.target.value);
              const s = sessions.find((item) => item.session_id === e.target.value);
              if (s) {
                setTargetDay(s.day);
                setTargetPeriod(s.start_period);
                setTargetRoom(s.room_id);
              }
            }}
            className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-brand-500"
          >
            {displaySessions.map((s) => (
              <option key={s.session_id} value={s.session_id}>
                {s.session_id}: {s.course_code} ({s.type}) • Group: {s.group_id} • Faculty: {s.faculty_id} [Currently: {s.day} P{s.start_period} in {s.room_id}]
              </option>
            ))}
          </select>
        </div>

        {/* Current Placement Details */}
        {activeSession && (
          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/50 border border-slate-200/50 dark:border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Course Code</span>
              <strong className="text-slate-900 dark:text-white">{activeSession.course_code}</strong>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Student Group</span>
              <strong className="text-slate-900 dark:text-white">{activeSession.group_id}</strong>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Faculty</span>
              <strong className="text-slate-900 dark:text-white">{activeSession.faculty_id}</strong>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Duration</span>
              <strong className="text-slate-900 dark:text-white">{activeSession.duration} Period(s)</strong>
            </div>
          </div>
        )}

        {/* Step 2: Choose Target Slot */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
            2. Choose Desired Target Slot & Venue
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1">
                Target Day
              </label>
              <select
                value={targetDay}
                onChange={(e) => setTargetDay(e.target.value as DayOfWeek)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none"
              >
                {DAYS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1">
                Target Start Period
              </label>
              <select
                value={targetPeriod}
                onChange={(e) => setTargetPeriod(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none"
              >
                {PERIODS.map((p) => (
                  <option key={p} value={p}>
                    Period {p} ({p + 7}:00 - {p + 8}:00)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1">
                Target Room
              </label>
              <select
                value={targetRoom}
                onChange={(e) => setTargetRoom(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none"
              >
                {rooms.map((r) => (
                  <option key={r.room_id} value={r.room_id}>
                    {r.room_id} ({r.type} - Cap: {r.capacity})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Validation Result Box */}
        <div className="pt-2">
          {validating ? (
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-xs text-slate-400 flex items-center space-x-2">
              <RefreshCw className="w-4 h-4 animate-spin text-brand-500" />
              <span>Verifying against CP-SAT hard constraint matrix...</span>
            </div>
          ) : validationResult?.is_valid ? (
            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-800 dark:text-emerald-300 text-xs space-y-2">
              <div className="flex items-center space-x-2 font-bold">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Move Valid! (0 Hard Violations)</span>
              </div>
              <p className="text-[11px] text-emerald-700 dark:text-emerald-400">
                Faculty, student group, and room are free. Capacity satisfies group strength. Lunch break gap respected.
              </p>
            </div>
          ) : (
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-800 dark:text-rose-300 text-xs space-y-2">
              <div className="flex items-center space-x-2 font-bold">
                <AlertTriangle className="w-4 h-4 text-rose-500" />
                <span>Move Infeasible (Hard Violations Detected)</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-rose-700 dark:text-rose-400">
                {validationResult?.hard_violations?.map((v, i) => (
                  <li key={i}>{v}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {commitMessage && (
          <div className="p-4 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-700 dark:text-brand-300 text-xs font-semibold">
            {commitMessage}
          </div>
        )}

        {/* Step 3: Action Button */}
        <div className="flex justify-end pt-2">
          <button
            onClick={handleCommitMove}
            disabled={!validationResult?.is_valid || committing}
            className="px-6 py-3 rounded-2xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs transition-colors flex items-center space-x-2 disabled:opacity-40 shadow-lg shadow-brand-500/20 active:scale-95"
          >
            {committing ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : isCoordinator ? (
              <>
                <SendHorizontal className="w-4 h-4" />
                <span>Submit Relocation Request to Admin</span>
              </>
            ) : (
              <>
                <ShieldCheck className="w-4 h-4" />
                <span>Commit Safe Move to Master Schedule</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
