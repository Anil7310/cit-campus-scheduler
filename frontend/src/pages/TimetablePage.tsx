import React, { useEffect, useState, useMemo } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { TimetableSession, StudentGroup, Faculty, Room, DayOfWeek } from '../types';
import { ExplainModal } from '../components/ExplainModal';
import {
  Calendar,
  Filter,
  Download,
  Users,
  GraduationCap,
  Building2,
  Sparkles,
  Info,
  Clock,
  CheckCircle,
  AlertCircle,
  ShieldAlert
} from 'lucide-react';

const DAYS: DayOfWeek[] = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
const PERIODS = [1, 2, 3, 4, 5, 6, 7, 8, 9];

const PERIOD_TIMES: Record<number, string> = {
  1: '08:00 - 09:00',
  2: '09:00 - 10:00',
  3: '10:00 - 11:00',
  4: '11:00 - 12:00',
  5: '12:00 - 13:00',
  6: '13:00 - 14:00',
  7: '14:00 - 15:00',
  8: '15:00 - 16:00',
  9: '16:00 - 17:00',
};

export const TimetablePage: React.FC = () => {
  const { user } = useAuth();
  const isCoordinator = user?.role === 'coordinator';
  const coordDept = (user?.department || 'CSE').toUpperCase();

  const [sessions, setSessions] = useState<TimetableSession[]>([]);
  const [groups, setGroups] = useState<StudentGroup[]>([]);
  const [faculty, setFaculty] = useState<Faculty[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);

  // Department-scoped collections for coordinator
  const scopedGroups = useMemo(() => {
    if (!isCoordinator) return groups;
    return groups.filter(
      (g) =>
        g.department?.toUpperCase() === coordDept ||
        g.group_id?.toUpperCase().includes(coordDept)
    );
  }, [groups, isCoordinator, coordDept]);

  const scopedFaculty = useMemo(() => {
    if (!isCoordinator) return faculty;
    return faculty.filter((f) => f.department?.toUpperCase() === coordDept);
  }, [faculty, isCoordinator, coordDept]);

  // Filters & State
  const [viewMode, setViewMode] = useState<'group' | 'faculty' | 'room'>('group');
  const [selectedEntity, setSelectedEntity] = useState<string>('CSE-Y1');
  const [scheduleType, setScheduleType] = useState<'baseline' | 'after'>('baseline');
  const [filterType, setFilterType] = useState<string>('ALL');

  // Modal explanation state
  const [selectedSessionForExplain, setSelectedSessionForExplain] = useState<string | null>(null);

  // Fetch initial data
  useEffect(() => {
    const loadResources = async () => {
      setLoading(true);
      try {
        const [gList, fList, rList] = await Promise.all([
          api.getGroups(),
          api.getFaculty(),
          api.getRooms(),
        ]);
        setGroups(gList);
        setFaculty(fList);
        setRooms(rList);

        const initialGroups = isCoordinator
          ? gList.filter(
              (g) =>
                g.department?.toUpperCase() === coordDept ||
                g.group_id?.toUpperCase().includes(coordDept)
            )
          : gList;

        if (initialGroups.length > 0) {
          setSelectedEntity(initialGroups[0].group_id);
        } else if (gList.length > 0) {
          setSelectedEntity(gList[0].group_id);
        }
      } catch (e) {
        console.error(e);
      }
    };
    loadResources();
  }, [isCoordinator, coordDept]);

  // Fetch sessions based on scheduleType
  useEffect(() => {
    const loadSchedule = async () => {
      setLoading(true);
      try {
        const res =
          scheduleType === 'after'
            ? await api.getScheduleAfter()
            : await api.getSchedule();
        setSessions(res.sessions || []);
      } catch (e) {
        console.error('Failed to load schedule', e);
      } finally {
        setLoading(false);
      }
    };
    loadSchedule();
  }, [scheduleType]);

  // Update selected entity when viewMode changes
  const handleViewModeChange = (mode: 'group' | 'faculty' | 'room') => {
    setViewMode(mode);
    if (mode === 'group' && scopedGroups.length > 0) setSelectedEntity(scopedGroups[0].group_id);
    else if (mode === 'faculty' && scopedFaculty.length > 0) setSelectedEntity(scopedFaculty[0].faculty_id);
    else if (mode === 'room' && rooms.length > 0) setSelectedEntity(rooms[0].room_id);
  };

  // Filtered sessions for the selected entity
  const visibleSessions = useMemo(() => {
    return sessions.filter((s) => {
      // Entity match
      let matchesEntity = false;
      if (viewMode === 'group') matchesEntity = s.group_id === selectedEntity;
      else if (viewMode === 'faculty') matchesEntity = s.faculty_id === selectedEntity;
      else if (viewMode === 'room') matchesEntity = s.room_id === selectedEntity;

      if (!matchesEntity) return false;

      // Filter type
      if (filterType !== 'ALL' && s.type !== filterType) return false;

      return true;
    });
  }, [sessions, viewMode, selectedEntity, filterType]);

  // Map day -> period -> session for grid rendering
  const gridMap = useMemo(() => {
    const map: Record<string, Record<number, TimetableSession>> = {};
    DAYS.forEach((d) => {
      map[d] = {};
    });

    visibleSessions.forEach((s) => {
      for (let p = s.start_period; p < s.start_period + s.duration; p++) {
        if (map[s.day]) {
          map[s.day][p] = s;
        }
      }
    });

    return map;
  }, [visibleSessions]);

  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(visibleSessions, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cit_schedule_${viewMode}_${selectedEntity}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header with Title and Mode Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
              CIT Master Timetable
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
              Spring 2026
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Clash-free weekly grid generated by OR-Tools CP-SAT with 0 hard violations.
          </p>
        </div>

        {/* Schedule Version Switcher: Baseline vs Post-Disruption */}
        <div className="flex items-center space-x-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-2xl border border-slate-200/80 dark:border-slate-700">
          <button
            onClick={() => setScheduleType('baseline')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              scheduleType === 'baseline'
                ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-sm'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Baseline Schedule
          </button>
          <button
            onClick={() => setScheduleType('after')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              scheduleType === 'after'
                ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-sm'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Post-Disruption Schedule
          </button>
        </div>
      </div>

      {/* Coordinator Scope Notification */}
      {isCoordinator && (
        <div className="p-3.5 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800 flex items-center justify-between text-xs text-indigo-900 dark:text-indigo-200">
          <div className="flex items-center space-x-2 font-semibold">
            <ShieldAlert className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
            <span>🏛️ Department Coordinator Scope: Scoped strictly to {coordDept} batches and faculty. Schedule edits require Admin approval.</span>
          </div>
          <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-indigo-200/60 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-300">
            {coordDept} Department
          </span>
        </div>
      )}

      {/* Control Bar: View Mode, Entity Dropdown, Filter, Export */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-wrap items-center justify-between gap-4">
        {/* Mode Tabs */}
        <div className="flex items-center space-x-1.5 bg-slate-50 dark:bg-slate-950 p-1 rounded-xl border border-slate-200/60 dark:border-slate-800">
          <button
            onClick={() => handleViewModeChange('group')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewMode === 'group'
                ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            <Users className="w-3.5 h-3.5 text-indigo-500" />
            <span>By Student Group</span>
          </button>
          <button
            onClick={() => handleViewModeChange('faculty')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewMode === 'faculty'
                ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            <GraduationCap className="w-3.5 h-3.5 text-emerald-500" />
            <span>By Faculty</span>
          </button>
          <button
            onClick={() => handleViewModeChange('room')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewMode === 'room'
                ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            <Building2 className="w-3.5 h-3.5 text-amber-500" />
            <span>By Room</span>
          </button>
        </div>

        {/* Entity Selector Dropdown */}
        <div className="flex items-center space-x-3">
          <label className="text-xs font-semibold text-slate-500 dark:text-slate-400">
            {viewMode === 'group' && 'Select Group:'}
            {viewMode === 'faculty' && 'Select Faculty:'}
            {viewMode === 'room' && 'Select Room:'}
          </label>
          <select
            value={selectedEntity}
            onChange={(e) => setSelectedEntity(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-brand-500"
          >
            {viewMode === 'group' &&
              scopedGroups.map((g) => (
                <option key={g.group_id} value={g.group_id}>
                  {g.name} ({g.department} Y{g.year} - {g.strength} students)
                </option>
              ))}
            {viewMode === 'faculty' &&
              scopedFaculty.map((f) => (
                <option key={f.faculty_id} value={f.faculty_id}>
                  {f.faculty_id}: {f.name} ({f.department})
                </option>
              ))}
            {viewMode === 'room' &&
              rooms.map((r) => (
                <option key={r.room_id} value={r.room_id}>
                  {r.room_id} ({r.type} - Cap: {r.capacity})
                </option>
              ))}
          </select>
        </div>

        {/* Type Filter & Export */}
        <div className="flex items-center space-x-2">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs text-slate-700 dark:text-slate-300 outline-none"
          >
            <option value="ALL">All Session Types</option>
            <option value="LECTURE">Lectures Only</option>
            <option value="LAB">Labs Only</option>
            <option value="TUTORIAL">Tutorials Only</option>
          </select>

          <button
            onClick={handleDownloadJson}
            className="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors flex items-center space-x-1.5"
            title="Download JSON schedule for this view"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {/* Timetable Interactive Grid */}
      <div className="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse min-w-[900px]">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-950 border-b border-slate-200/80 dark:border-slate-800 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-4 text-left w-24">Day</th>
                {PERIODS.map((p) => (
                  <th
                    key={p}
                    className={`py-3 px-2 text-center ${
                      p === 5 ? 'border-r-2 border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/30 dark:bg-indigo-950/20' : ''
                    }`}
                  >
                    <div>P{p}</div>
                    <div className="text-[9px] font-normal text-slate-400">
                      {PERIOD_TIMES[p]}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {DAYS.map((day) => {
                let skipPeriods = 0;
                return (
                  <tr key={day} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/20 transition-colors">
                    {/* Day Column */}
                    <td className="py-4 px-4 font-bold text-xs text-slate-800 dark:text-slate-200 bg-slate-50/30 dark:bg-slate-950/20">
                      {day}
                    </td>

                    {/* Periods P1 - P9 */}
                    {PERIODS.map((period) => {
                      if (skipPeriods > 0) {
                        skipPeriods--;
                        return null; // Spanned by previous multi-period session
                      }

                      const session = gridMap[day]?.[period];
                      const isStartOfSession = session && session.start_period === period;
                      const span = isStartOfSession ? session.duration : 1;

                      if (isStartOfSession && span > 1) {
                        skipPeriods = span - 1;
                      }

                      const isLunchDivider = period === 5;

                      if (!session) {
                        return (
                          <td
                            key={period}
                            colSpan={1}
                            className={`p-1.5 text-center align-middle ${
                              isLunchDivider
                                ? 'border-r-2 border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/10'
                                : ''
                            }`}
                          >
                            <div className="h-16 rounded-xl border border-dashed border-slate-100 dark:border-slate-800/80 flex items-center justify-center text-[10px] text-slate-300 dark:text-slate-700 select-none">
                              Free
                            </div>
                          </td>
                        );
                      }

                      if (!isStartOfSession) {
                        // Handled by colSpan of start period
                        return null;
                      }

                      // Render active session card
                      const isLab = session.type === 'LAB';
                      const isTut = session.type === 'TUTORIAL';
                      const isDisrupted = session.is_disrupted;

                      return (
                        <td
                          key={period}
                          colSpan={span}
                          className={`p-1.5 align-middle ${
                            period + span - 1 === 5
                              ? 'border-r-2 border-indigo-200 dark:border-indigo-900/60'
                              : ''
                          }`}
                        >
                          <div
                            onClick={() => setSelectedSessionForExplain(session.session_id)}
                            className={`h-16 rounded-xl p-2 cursor-pointer transition-all transform hover:scale-[1.02] hover:shadow-md border flex flex-col justify-between text-left ${
                              isDisrupted
                                ? 'bg-amber-500/10 border-amber-500/30 text-amber-900 dark:text-amber-200'
                                : isLab
                                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-900 dark:text-emerald-200'
                                : isTut
                                ? 'bg-purple-500/10 border-purple-500/30 text-purple-900 dark:text-purple-200'
                                : 'bg-brand-500/10 border-brand-500/30 text-brand-900 dark:text-brand-200'
                            }`}
                            title="Click to explain placement"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-extrabold text-[11px] truncate">
                                {session.course_code}
                              </span>
                              <span className="text-[9px] font-bold px-1.5 py-0.2 rounded-md bg-white/70 dark:bg-black/30">
                                {session.type}
                              </span>
                            </div>

                            <div className="flex items-center justify-between text-[10px] opacity-90 truncate">
                              <span>
                                {viewMode === 'group'
                                  ? `${session.room_id} • ${session.faculty_id}`
                                  : viewMode === 'faculty'
                                  ? `${session.room_id} • ${session.group_id}`
                                  : `${session.group_id} • ${session.faculty_id}`}
                              </span>
                              {isDisrupted && (
                                <span className="text-[8px] font-black uppercase text-amber-600 bg-amber-100 dark:bg-amber-950 px-1 rounded">
                                  Moved
                                </span>
                              )}
                            </div>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Legend Footer */}
        <div className="p-4 bg-slate-50 dark:bg-slate-950/60 border-t border-slate-200/80 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-md bg-brand-500/20 border border-brand-500/50" />
              <span>Lecture (1 hr)</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-md bg-emerald-500/20 border border-emerald-500/50" />
              <span>Lab (2 hrs continuous)</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-md bg-purple-500/20 border border-purple-500/50" />
              <span>Tutorial</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-md bg-amber-500/20 border border-amber-500/50" />
              <span>Disrupted / Re-routed</span>
            </span>
          </div>

          <div className="flex items-center space-x-1 text-[11px] text-slate-400">
            <Info className="w-3.5 h-3.5" />
            <span>Click any session card for instant CP-SAT constraint explanation</span>
          </div>
        </div>
      </div>

      {/* Solver Decision Explanation Modal */}
      <ExplainModal
        sessionId={selectedSessionForExplain}
        onClose={() => setSelectedSessionForExplain(null)}
      />
    </div>
  );
};
