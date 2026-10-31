import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  GraduationCap,
  Calendar,
  Clock,
  MapPin,
  BookOpen,
  Award,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Send,
  X,
  RefreshCw,
  PlusCircle,
  CalendarCheck,
  Building,
  UserCheck
} from 'lucide-react';

interface FacultyProfile {
  id: string;
  name: string;
  department: string;
  email: string;
  cabin: string;
  phone: string;
  qualifications: string[];
  fields_of_interest: string[];
  teaching_subjects: {
    code: string;
    name: string;
    sessions_per_week: number;
    hours_per_week: number;
    groups: string[];
  }[];
  total_weekly_hours: number;
  max_allowed_hours: number;
}

interface LectureSession {
  session_id: string;
  course_code: string;
  course_name: string;
  session_type: string;
  group_id: string;
  student_groups: string[];
  room_id: string;
  day: string;
  start_period: number;
  duration: number;
  time_slot: string;
  status: string;
  note?: string | null;
}

interface ScheduleData {
  faculty_id: string;
  faculty_name: string;
  total_lectures: number;
  total_contact_hours: number;
  schedule_by_day: Record<string, LectureSession[]>;
}

export const FacultyPortalPage: React.FC = () => {
  const [profile, setProfile] = useState<FacultyProfile | null>(null);
  const [schedule, setSchedule] = useState<ScheduleData | null>(null);
  const [activeRequests, setActiveRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDay, setSelectedDay] = useState<string>('MON');

  // Modal states for lecture modification (Cancel / Reschedule)
  const [selectedLecture, setSelectedLecture] = useState<LectureSession | null>(null);
  const [actionType, setActionType] = useState<'CANCEL' | 'RESCHEDULE'>('CANCEL');
  const [actionReason, setActionReason] = useState('');
  const [targetDay, setTargetDay] = useState('TUE');
  const [targetPeriod, setTargetPeriod] = useState(4);
  const [targetRoom, setTargetRoom] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Vacant slots for student batch
  const [vacantSlots, setVacantSlots] = useState<any[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);

  const fetchVacantSlotsForBatch = async (groupId: string, sessionType: string, duration: number) => {
    setLoadingSlots(true);
    try {
      const res = await api.getVacantSlots({
        group_id: groupId,
        session_type: sessionType,
        duration: duration,
      });
      setVacantSlots(res.vacant_slots || []);
    } catch (err) {
      console.error('Failed to fetch vacant slots for batch:', err);
      setVacantSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  // Modal state for Weekend extra lecture request
  const [showWeekendModal, setShowWeekendModal] = useState(false);
  const [weekendSubject, setWeekendSubject] = useState('');
  const [weekendDay, setWeekendDay] = useState<'SAT' | 'SUN'>('SAT');
  const [weekendPeriod, setWeekendPeriod] = useState(2);
  const [weekendDuration, setWeekendDuration] = useState(1);
  const [weekendRoom, setWeekendRoom] = useState('LH-1');
  const [weekendReason, setWeekendReason] = useState('');
  const [weekendLoading, setWeekendLoading] = useState(false);
  const [weekendError, setWeekendError] = useState<string | null>(null);
  const [weekendSuccess, setWeekendSuccess] = useState<string | null>(null);

  // Pre-submission Availability Checks
  const [weekendAvailability, setWeekendAvailability] = useState<{ is_available: boolean; reason: string } | null>(null);
  const [checkingWeekendAvail, setCheckingWeekendAvail] = useState(false);

  const [rescheduleAvailability, setRescheduleAvailability] = useState<{ is_available: boolean; reason: string } | null>(null);
  const [checkingRescheduleAvail, setCheckingRescheduleAvail] = useState(false);

  // Pre-check weekend availability
  useEffect(() => {
    if (!showWeekendModal || !weekendRoom.trim() || !weekendDay || !weekendPeriod) {
      setWeekendAvailability(null);
      return;
    }
    setCheckingWeekendAvail(true);
    let mounted = true;
    api
      .checkBookingAvailability({
        day: weekendDay,
        start_period: weekendPeriod,
        duration: weekendDuration,
        room_id: weekendRoom.trim(),
      })
      .then((res: any) => {
        if (mounted) setWeekendAvailability(res);
      })
      .catch((err) => {
        console.error('Weekend availability check failed:', err);
      })
      .finally(() => {
        if (mounted) setCheckingWeekendAvail(false);
      });
    return () => {
      mounted = false;
    };
  }, [showWeekendModal, weekendRoom, weekendDay, weekendPeriod, weekendDuration]);

  // Pre-check reschedule target slot availability
  useEffect(() => {
    if (actionType !== 'RESCHEDULE' || !targetRoom.trim() || !targetDay || !targetPeriod || !selectedLecture) {
      setRescheduleAvailability(null);
      return;
    }
    setCheckingRescheduleAvail(true);
    let mounted = true;
    api
      .checkBookingAvailability({
        day: targetDay,
        start_period: targetPeriod,
        duration: selectedLecture.duration,
        room_id: targetRoom.trim(),
      })
      .then((res: any) => {
        if (mounted) setRescheduleAvailability(res);
      })
      .catch((err) => {
        console.error('Reschedule availability check failed:', err);
      })
      .finally(() => {
        if (mounted) setCheckingRescheduleAvail(false);
      });
    return () => {
      mounted = false;
    };
  }, [actionType, targetRoom, targetDay, targetPeriod, selectedLecture]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [prof, sched, reqs] = await Promise.all([
        api.getFacultyProfile().catch(() => null),
        api.getFacultySchedule().catch(() => null),
        api.getFacultyRequests().catch(() => []),
      ]);
      setProfile(prof);
      setSchedule(sched);
      setActiveRequests(reqs || []);
      if (prof?.teaching_subjects?.length && !weekendSubject) {
        setWeekendSubject(prof.teaching_subjects[0].code);
      }
    } catch (err) {
      console.error('Error fetching faculty data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleOpenLectureModal = (lecture: LectureSession) => {
    setSelectedLecture(lecture);
    setActionType('CANCEL');
    setActionReason('');
    setTargetDay(lecture.day === 'MON' ? 'TUE' : 'MON');
    setTargetPeriod(lecture.start_period);
    setTargetRoom(lecture.room_id);
    setActionError(null);
    setActionSuccess(null);
    fetchVacantSlotsForBatch(lecture.group_id, lecture.session_type, lecture.duration);
  };

  const handleLectureActionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLecture) return;
    if (!actionReason.trim()) {
      setActionError('Please provide a proper reason for this action.');
      return;
    }

    setActionLoading(true);
    setActionError(null);
    try {
      await api.modifyLecture({
        session_id: selectedLecture.session_id,
        action: actionType,
        reason: actionReason.trim(),
        target_day: actionType === 'RESCHEDULE' ? targetDay : undefined,
        target_period: actionType === 'RESCHEDULE' ? targetPeriod : undefined,
        target_room: actionType === 'RESCHEDULE' ? targetRoom : undefined,
      });

      setActionSuccess(
        actionType === 'CANCEL'
          ? `Lecture ${selectedLecture.course_code} cancellation submitted successfully.`
          : `Reschedule request submitted for ${selectedLecture.course_code} to ${targetDay} Period ${targetPeriod}.`
      );

      setTimeout(() => {
        setSelectedLecture(null);
        loadAllData();
      }, 1200);
    } catch (err: any) {
      setActionError(err.message || 'Action failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleWeekendSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!weekendReason.trim()) {
      setWeekendError('Please provide a legitimate reason for requesting weekend extra lecture.');
      return;
    }

    // Weekly planned limit validation
    if (profile) {
      const currentPlanned = profile.total_weekly_hours || 0;
      const limit = profile.max_allowed_hours || 16;
      if (currentPlanned + weekendDuration > limit) {
        setWeekendError(
          `Weekly Planned Limit Exceeded: Current weekly teaching is ${currentPlanned} hrs. Adding ${weekendDuration} hr(s) exceeds maximum weekly limit of ${limit} hrs!`
        );
        return;
      }
    }

    setWeekendLoading(true);
    setWeekendError(null);
    try {
      await api.requestWeekendLecture({
        subject_code: weekendSubject,
        day: weekendDay,
        start_period: weekendPeriod,
        duration: weekendDuration,
        room_id: weekendRoom,
        reason: weekendReason.trim(),
      });

      setWeekendSuccess(`Weekend lecture request submitted to Dean & Admin for approval.`);
      setTimeout(() => {
        setShowWeekendModal(false);
        setWeekendReason('');
        loadAllData();
      }, 1400);
    } catch (err: any) {
      setWeekendError(err.message || 'Failed to submit weekend request');
    } finally {
      setWeekendLoading(false);
    }
  };

  const days = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
  const dayLabels: Record<string, string> = {
    MON: 'Monday',
    TUE: 'Tuesday',
    WED: 'Wednesday',
    THU: 'Thursday',
    FRI: 'Friday',
  };

  const currentDayLectures = schedule?.schedule_by_day?.[selectedDay] || [];

  return (
    <div className="space-y-6">
      {/* Top Banner / Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <img
              src="/logo.jpg"
              alt="CIT Logo"
              className="w-12 h-12 rounded-full object-cover shadow-sm ring-2 ring-emerald-500/30 bg-white shrink-0"
            />
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                Faculty Workspace & Academic Portal
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Personalized faculty profile, daily timetable schedule, lecture change portal & weekend requests
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowWeekendModal(true)}
            className="px-3.5 py-2 text-xs font-semibold text-white bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 rounded-xl flex items-center space-x-1.5 shadow-md shadow-brand-500/20 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Request Weekend Extra Lecture</span>
          </button>
          <button
            onClick={loadAllData}
            disabled={loading}
            className="p-2 text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl hover:bg-slate-50 shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Faculty Profile Card */}
      {profile && (
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Bio & Contacts */}
            <div className="lg:col-span-1 space-y-4 border-b lg:border-b-0 lg:border-r border-slate-100 dark:border-slate-800 lg:pr-6">
              <div className="flex items-center space-x-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-500 to-emerald-600 flex items-center justify-center text-white text-xl font-extrabold shadow-lg shadow-brand-500/20">
                  {profile.name.charAt(0)}
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white leading-tight">
                    {profile.name}
                  </h2>
                  <span className="inline-block mt-0.5 px-2 py-0.5 rounded-md bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-300 font-bold text-[11px] border border-brand-200 dark:border-brand-800">
                    ID: {profile.id} • {profile.department}
                  </span>
                </div>
              </div>

              <div className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
                <div className="flex items-center space-x-2">
                  <Building className="w-4 h-4 text-slate-400" />
                  <span>Cabin: <strong>{profile.cabin}</strong></span>
                </div>
                <div className="flex items-center space-x-2">
                  <Send className="w-4 h-4 text-slate-400" />
                  <span>Email: <strong>{profile.email}</strong></span>
                </div>
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-slate-400" />
                  <span>
                    Planned Contact: <strong>{profile.total_weekly_hours} hrs/week</strong> (Max limit: {profile.max_allowed_hours} hrs)
                  </span>
                </div>
              </div>

              {/* Progress bar for weekly workload */}
              <div>
                <div className="flex justify-between text-[11px] font-medium text-slate-500 mb-1">
                  <span>Weekly Contact Load</span>
                  <span>{Math.round((profile.total_weekly_hours / profile.max_allowed_hours) * 100)}%</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-emerald-500 h-2 rounded-full transition-all"
                    style={{ width: `${Math.min(100, (profile.total_weekly_hours / profile.max_allowed_hours) * 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Middle: Qualifications & Fields of Interest */}
            <div className="lg:col-span-1 space-y-4 border-b lg:border-b-0 lg:border-r border-slate-100 dark:border-slate-800 lg:pr-6">
              <div>
                <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-2">
                  <Award className="w-4 h-4 text-emerald-500" />
                  <span>Academic Qualifications</span>
                </div>
                <ul className="space-y-1.5">
                  {profile.qualifications?.map((q, idx) => (
                    <li key={idx} className="text-xs text-slate-600 dark:text-slate-300 flex items-start space-x-1.5">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>{q}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-2">
                  <Sparkles className="w-4 h-4 text-amber-500" />
                  <span>Fields of Interest & Research</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {profile.fields_of_interest?.map((f, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-[11px] font-medium text-slate-700 dark:text-slate-300"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: Teaching Subjects */}
            <div className="lg:col-span-1 space-y-3">
              <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-1">
                <BookOpen className="w-4 h-4 text-brand-500" />
                <span>Current Teaching Subjects</span>
              </div>
              <div className="space-y-2.5">
                {profile.teaching_subjects?.map((sub) => (
                  <div
                    key={sub.code}
                    className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-brand-600 dark:text-brand-400">
                        {sub.code}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-100 dark:bg-brand-950/60 text-brand-700 dark:text-brand-300 font-semibold">
                        {sub.hours_per_week} hrs / {sub.sessions_per_week} classes
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 mt-1">
                      {sub.name}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      Groups: {sub.groups.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Timetable Section according to Day */}
      <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center space-x-2">
              <Calendar className="w-5 h-5 text-brand-500" />
              <span>Daily Lecture Timetable</span>
            </h2>
            <p className="text-xs text-slate-500">
              Click on any scheduled lecture card to open the action portal (Cancel or Reschedule)
            </p>
          </div>

          {/* Day selection tabs */}
          <div className="inline-flex p-1 bg-slate-100 dark:bg-slate-800 rounded-2xl">
            {days.map((d) => {
              const count = schedule?.schedule_by_day?.[d]?.length || 0;
              const isSelected = selectedDay === d;
              return (
                <button
                  key={d}
                  onClick={() => setSelectedDay(d)}
                  className={`px-3.5 py-1.5 text-xs font-bold rounded-xl transition-all flex items-center space-x-1.5 ${
                    isSelected
                      ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-white shadow-sm'
                      : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                  }`}
                >
                  <span>{dayLabels[d]}</span>
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                      isSelected
                        ? 'bg-brand-100 dark:bg-brand-900 text-brand-700 dark:text-brand-300'
                        : 'bg-slate-200 dark:bg-slate-600 text-slate-600 dark:text-slate-300'
                    }`}
                  >
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Schedule grid for current day */}
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin text-brand-500 mx-auto mb-2" />
            <span className="text-xs">Loading faculty timetable...</span>
          </div>
        ) : currentDayLectures.length === 0 ? (
          <div className="p-12 text-center bg-slate-50 dark:bg-slate-800/40 rounded-2xl border border-dashed border-slate-200 dark:border-slate-700">
            <CalendarCheck className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No Lectures on {dayLabels[selectedDay]}
            </h4>
            <p className="text-xs text-slate-400 mt-1">
              You have no scheduled teaching commitments on this day. Great time for research and student mentoring!
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {currentDayLectures.map((lec) => {
              const isCancelled = lec.status === 'CANCELLED';
              const isRescheduled = lec.status === 'RESCHEDULED';

              return (
                <div
                  key={lec.session_id}
                  onClick={() => !isCancelled && handleOpenLectureModal(lec)}
                  className={`p-5 rounded-2xl border transition-all cursor-pointer relative overflow-hidden group ${
                    isCancelled
                      ? 'bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-800 opacity-60 cursor-not-allowed'
                      : isRescheduled
                      ? 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900/50 hover:shadow-md'
                      : 'bg-white dark:bg-slate-900 border-slate-200/80 dark:border-slate-800 hover:border-brand-500 hover:shadow-md'
                  }`}
                >
                  {/* Top status bar */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="px-2.5 py-1 rounded-lg bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 font-extrabold text-xs border border-brand-200 dark:border-brand-800">
                      {lec.course_code}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        isCancelled
                          ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300'
                          : isRescheduled
                          ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                          : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
                      }`}
                    >
                      {lec.status}
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 dark:text-white text-sm mb-1 leading-snug">
                    {lec.course_name}
                  </h3>

                  <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300 mt-3">
                    <div className="flex items-center space-x-2">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>{lec.time_slot}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span>Room: <strong>{lec.room_id}</strong></span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <GraduationCap className="w-3.5 h-3.5 text-slate-400" />
                      <span>Group: <strong>{lec.group_id}</strong> ({lec.session_type})</span>
                    </div>
                  </div>

                  {lec.note && (
                    <div className="mt-3 p-2 bg-slate-100 dark:bg-slate-800 rounded-lg text-[11px] text-slate-500 italic">
                      Note: {lec.note}
                    </div>
                  )}

                  {!isCancelled && (
                    <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] font-semibold text-brand-600 dark:text-brand-400">
                      <span>Click to Modify / Reschedule</span>
                      <span className="group-hover:translate-x-1 transition-transform">→</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Active Requests Tracker */}
      {activeRequests.length > 0 && (
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-2">
            <Clock className="w-5 h-5 text-indigo-500" />
            <span>Active Modification & Weekend Requests</span>
          </h2>
          <div className="space-y-2">
            {activeRequests.map((req, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-xs text-slate-900 dark:text-white">
                      {req.action_type || 'WEEKEND_EXTRA'} - {req.course_code || req.subject_code}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 font-bold">
                      {req.status || 'SUBMITTED'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Reason: "{req.reason}"</p>
                </div>
                <div className="text-right text-[11px] text-slate-400">
                  {req.created_at ? new Date(req.created_at).toLocaleString() : 'Recent'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* LECTURE MODIFICATION MODAL (Portal) */}
      {selectedLecture && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Modify Lecture - {selectedLecture.course_code}
                </h3>
                <p className="text-xs text-slate-400">
                  {selectedLecture.course_name} • {selectedLecture.time_slot} ({selectedLecture.room_id})
                </p>
              </div>
              <button
                onClick={() => setSelectedLecture(null)}
                className="p-1.5 rounded-xl text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleLectureActionSubmit} className="p-6 space-y-4">
              {actionError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{actionError}</span>
                </div>
              )}

              {actionSuccess && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{actionSuccess}</span>
                </div>
              )}

              {/* Action type switcher */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Select Action
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setActionType('CANCEL')}
                    className={`py-2 text-xs font-bold rounded-xl border transition-all ${
                      actionType === 'CANCEL'
                        ? 'bg-rose-50 border-rose-300 text-rose-700 dark:bg-rose-950/50 dark:border-rose-800 dark:text-rose-300'
                        : 'border-slate-200 dark:border-slate-700 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    Cancel This Lecture
                  </button>
                  <button
                    type="button"
                    onClick={() => setActionType('RESCHEDULE')}
                    className={`py-2 text-xs font-bold rounded-xl border transition-all ${
                      actionType === 'RESCHEDULE'
                        ? 'bg-amber-50 border-amber-300 text-amber-700 dark:bg-amber-950/50 dark:border-amber-800 dark:text-amber-300'
                        : 'border-slate-200 dark:border-slate-700 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    Reschedule to Another Slot
                  </button>
                </div>
              </div>

              {/* Conditional Reschedule Parameters with Student Batch Vacant Slots Matching */}
              {actionType === 'RESCHEDULE' && (
                <div className="p-3.5 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-200 dark:border-slate-700 space-y-3.5">
                  
                  {/* Vacant Slots Section for Student Batch */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-[11px] font-bold text-slate-800 dark:text-slate-200 flex items-center space-x-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                        <span>Vacant Slots for Batch {selectedLecture.group_id}</span>
                      </label>
                      <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                        {vacantSlots.length} Clash-Free Slots Available
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      Click any vacant slot to automatically assign clash-free day, period, and room for batch <strong>{selectedLecture.group_id}</strong>:
                    </p>

                    {loadingSlots ? (
                      <div className="p-3 text-center text-xs text-slate-400 bg-white dark:bg-slate-900 rounded-xl">
                        <RefreshCw className="w-4 h-4 animate-spin text-brand-500 mx-auto mb-1" />
                        Scanning campus timetable for batch {selectedLecture.group_id}...
                      </div>
                    ) : vacantSlots.length === 0 ? (
                      <div className="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 text-xs">
                        No vacant regular slots found for this student batch.
                      </div>
                    ) : (
                      <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1">
                        {vacantSlots.slice(0, 10).map((slot, idx) => {
                          const isChosen =
                            targetDay === slot.day &&
                            targetPeriod === slot.start_period &&
                            targetRoom === slot.recommended_room;

                          return (
                            <button
                              key={idx}
                              type="button"
                              onClick={() => {
                                setTargetDay(slot.day);
                                setTargetPeriod(slot.start_period);
                                setTargetRoom(slot.recommended_room);
                              }}
                              className={`w-full p-2 rounded-xl border text-left transition-all flex items-center justify-between text-xs ${
                                isChosen
                                  ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-500 text-emerald-900 dark:text-emerald-200 ring-2 ring-emerald-500/20'
                                  : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-brand-400'
                              }`}
                            >
                              <div>
                                <span className="font-bold text-slate-900 dark:text-white mr-1.5">
                                  {slot.day} • {slot.time_slot} ({slot.period_label})
                                </span>
                                <span className="text-[10px] text-slate-500 dark:text-slate-400">
                                  Free Room: <strong className="text-brand-600 dark:text-brand-400">{slot.recommended_room}</strong> ({slot.room_type})
                                </span>
                              </div>
                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                  isChosen
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
                                }`}
                              >
                                {isChosen ? 'Selected' : 'Pick Slot'}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                      Selected Slot Parameters:
                    </span>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
                          Target Day
                        </label>
                        <select
                          value={targetDay}
                          onChange={(e) => setTargetDay(e.target.value)}
                          className="w-full text-xs p-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                        >
                          {days.map((d) => (
                            <option key={d} value={d}>
                              {dayLabels[d]}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
                          Target Period
                        </label>
                        <select
                          value={targetPeriod}
                          onChange={(e) => setTargetPeriod(Number(e.target.value))}
                          className="w-full text-xs p-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                        >
                          <option value={1}>Period 1 (08:00 - 09:00)</option>
                          <option value={2}>Period 2 (09:00 - 10:00)</option>
                          <option value={3}>Period 3 (10:00 - 11:00)</option>
                          <option value={4}>Period 4 (11:00 - 12:00)</option>
                          <option value={6}>Period 6 (13:00 - 14:00)</option>
                          <option value={7}>Period 7 (14:00 - 15:00)</option>
                          <option value={8}>Period 8 (15:00 - 16:00)</option>
                        </select>
                      </div>
                    </div>

                    <div className="mt-2">
                      <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
                        Assigned Vacant Room
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. LH-1, LH-2, CR-4"
                        value={targetRoom}
                        onChange={(e) => setTargetRoom(e.target.value)}
                        className="w-full text-xs p-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-semibold"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Mandatory Reason */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Reason for {actionType === 'CANCEL' ? 'Cancellation' : 'Rescheduling'} *
                </label>
                <textarea
                  required
                  rows={3}
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  placeholder="e.g. Medical emergency, urgent department research council meeting, university conference presentation..."
                  className="w-full text-xs p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                />
              </div>

              {/* Live Availability Pre-Check Status Banner for Rescheduling */}
              {actionType === 'RESCHEDULE' && targetRoom && (
                <div>
                  {checkingRescheduleAvail ? (
                    <div className="p-2.5 bg-slate-100 dark:bg-slate-800 rounded-xl text-xs text-slate-500 flex items-center space-x-2">
                      <Clock className="w-4 h-4 animate-spin text-brand-500 shrink-0" />
                      <span>Checking vacancy for {targetRoom} on {targetDay} Period {targetPeriod}...</span>
                    </div>
                  ) : rescheduleAvailability ? (
                    rescheduleAvailability.is_available ? (
                      <div className="p-2.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl flex items-center space-x-2 text-emerald-800 dark:text-emerald-200 text-xs">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>
                          <strong>Available & Clash-Free:</strong> Venue <strong>{targetRoom}</strong> is completely free on {targetDay} Period {targetPeriod}. Ready to submit!
                        </span>
                      </div>
                    ) : (
                      <div className="p-2.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl flex items-center space-x-2 text-rose-800 dark:text-rose-200 text-xs">
                        <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                        <span>
                          <strong>Not Available:</strong> {rescheduleAvailability.reason}
                        </span>
                      </div>
                    )
                  ) : null}
                </div>
              )}

              {/* Submit Buttons */}
              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedLecture(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 rounded-xl"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={
                    actionLoading ||
                    (actionType === 'RESCHEDULE' && rescheduleAvailability !== null && !rescheduleAvailability.is_available)
                  }
                  className={`px-4 py-2 text-xs font-bold text-white rounded-xl shadow-md transition-all flex items-center space-x-1.5 ${
                    actionType === 'RESCHEDULE' && rescheduleAvailability && !rescheduleAvailability.is_available
                      ? 'bg-slate-400 cursor-not-allowed opacity-60'
                      : actionType === 'CANCEL'
                      ? 'bg-rose-600 hover:bg-rose-500 shadow-rose-500/20'
                      : 'bg-brand-600 hover:bg-brand-500 shadow-brand-500/20'
                  }`}
                >
                  {actionLoading ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Send className="w-3.5 h-3.5" />
                  )}
                  <span>
                    {actionType === 'CANCEL'
                      ? 'Confirm Cancellation'
                      : actionType === 'RESCHEDULE' && rescheduleAvailability && !rescheduleAvailability.is_available
                      ? 'Slot Not Available'
                      : 'Submit Reschedule to Admin'}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* WEEKEND EXTRA LECTURE MODAL */}
      {showWeekendModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">
            <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Request Extra Lecture (Saturday / Sunday)
                </h3>
                <p className="text-xs text-slate-400">
                  Sends formal weekend slot booking to Admin for syllabus compensation
                </p>
              </div>
              <button
                onClick={() => setShowWeekendModal(false)}
                className="p-1.5 rounded-xl text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleWeekendSubmit} className="p-6 space-y-4">
              {weekendError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{weekendError}</span>
                </div>
              )}

              {weekendSuccess && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{weekendSuccess}</span>
                </div>
              )}

              {/* Curriculum Limit Guard Notice */}
              <div className="p-3 bg-amber-50 dark:bg-amber-950/30 rounded-xl border border-amber-200 dark:border-amber-900/50 text-amber-800 dark:text-amber-300 text-xs">
                <strong>Curriculum Guard:</strong> Extra lecture duration will be added to your current weekly load ({profile?.total_weekly_hours || 0} hrs). The total cannot exceed the weekly planned syllabus limit ({profile?.max_allowed_hours || 16} hrs).
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Subject for Extra Lecture
                </label>
                <select
                  value={weekendSubject}
                  onChange={(e) => setWeekendSubject(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-semibold"
                >
                  {profile?.teaching_subjects?.map((sub) => (
                    <option key={sub.code} value={sub.code}>
                      {sub.code} - {sub.name} ({sub.groups.join(', ')})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Weekend Day
                  </label>
                  <select
                    value={weekendDay}
                    onChange={(e) => setWeekendDay(e.target.value as any)}
                    className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-semibold"
                  >
                    <option value="SAT">Saturday</option>
                    <option value="SUN">Sunday</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Duration
                  </label>
                  <select
                    value={weekendDuration}
                    onChange={(e) => setWeekendDuration(Number(e.target.value))}
                    className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-semibold"
                  >
                    <option value={1}>1 Hour</option>
                    <option value={2}>2 Hours</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Time Slot
                  </label>
                  <select
                    value={weekendPeriod}
                    onChange={(e) => setWeekendPeriod(Number(e.target.value))}
                    className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                  >
                    <option value={2}>Morning: 09:00 - 10:00</option>
                    <option value={3}>Morning: 10:00 - 11:00</option>
                    <option value={4}>Morning: 11:00 - 12:00</option>
                    <option value={6}>Afternoon: 13:00 - 14:00</option>
                    <option value={7}>Afternoon: 14:00 - 15:00</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Preferred Room
                  </label>
                  <input
                    type="text"
                    value={weekendRoom}
                    onChange={(e) => setWeekendRoom(e.target.value)}
                    placeholder="LH-1 or AUD-1"
                    className="w-full text-xs p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Academic Justification / Reason *
                </label>
                <textarea
                  required
                  rows={3}
                  value={weekendReason}
                  onChange={(e) => setWeekendReason(e.target.value)}
                  placeholder="e.g. Remedial lecture to complete Unit 3 Algorithm Analysis before Midsem exams..."
                  className="w-full text-xs p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                />
              </div>

              {/* Live Availability Pre-Check Status Banner for Weekend Extra Lecture */}
              {weekendRoom && (
                <div>
                  {checkingWeekendAvail ? (
                    <div className="p-2.5 bg-slate-100 dark:bg-slate-800 rounded-xl text-xs text-slate-500 flex items-center space-x-2">
                      <Clock className="w-4 h-4 animate-spin text-brand-500 shrink-0" />
                      <span>Checking weekend room vacancy across campus...</span>
                    </div>
                  ) : weekendAvailability ? (
                    weekendAvailability.is_available ? (
                      <div className="p-2.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl flex items-center space-x-2 text-emerald-800 dark:text-emerald-200 text-xs">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>
                          <strong>Available & Clash-Free:</strong> Venue <strong>{weekendRoom}</strong> is completely free on {weekendDay} for {weekendDuration} hour(s). Ready to submit!
                        </span>
                      </div>
                    ) : (
                      <div className="p-2.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl flex items-center space-x-2 text-rose-800 dark:text-rose-200 text-xs">
                        <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                        <span>
                          <strong>Not Available:</strong> {weekendAvailability.reason}
                        </span>
                      </div>
                    )
                  ) : null}
                </div>
              )}

              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowWeekendModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={weekendLoading || (weekendAvailability !== null && !weekendAvailability.is_available)}
                  className={`px-4 py-2 text-xs font-bold text-white rounded-xl shadow-md transition-all flex items-center space-x-1.5 ${
                    weekendAvailability && !weekendAvailability.is_available
                      ? 'bg-slate-400 cursor-not-allowed opacity-60'
                      : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-500/20'
                  }`}
                >
                  {weekendLoading ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Send className="w-3.5 h-3.5" />
                  )}
                  <span>
                    {weekendAvailability && !weekendAvailability.is_available
                      ? 'Room Occupied / Not Available'
                      : 'Submit Request to Admin'}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

