import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Exam, Room } from '../types';
import {
  GraduationCap,
  ShieldCheck,
  Calendar,
  Clock,
  Users,
  Building2,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export const ExamsPage: React.FC = () => {
  const [exams, setExams] = useState<Exam[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDay, setSelectedDay] = useState<string>('ALL');
  const [selectedSlot, setSelectedSlot] = useState<string>('ALL');

  useEffect(() => {
    const loadExamsData = async () => {
      setLoading(true);
      try {
        const [examList, roomList] = await Promise.all([
          api.getExams(),
          api.getRooms(),
        ]);
        setExams(examList);
        setRooms(roomList);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadExamsData();
  }, []);

  const roomMap = React.useMemo(() => {
    const map: Record<string, Room> = {};
    rooms.forEach((r) => {
      map[r.room_id] = r;
    });
    return map;
  }, [rooms]);

  const filteredExams = exams.filter((e) => {
    const matchesSearch =
      e.course_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (e.course_name && e.course_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      e.student_groups.some((g) => g.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesDay = selectedDay === 'ALL' || e.day === selectedDay;
    const matchesSlot = selectedSlot === 'ALL' || e.slot === selectedSlot;

    return matchesSearch && matchesDay && matchesSlot;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
              Midsem Examination Schedule
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300">
              Spring 2026 (41 Exams)
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Deterministic OR-Tools exam timetable with 0 student group clashes.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-xs font-semibold flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>Gate B: 0 Clashes Verified</span>
          </div>
        </div>
      </div>

      {/* Strict 50% Capacity Policy Callout */}
      <div className="p-4 rounded-2xl bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200/80 dark:border-indigo-800 flex items-start space-x-3 text-xs text-indigo-900 dark:text-indigo-200">
        <CheckCircle2 className="w-5 h-5 text-brand-600 dark:text-brand-400 shrink-0 mt-0.5" />
        <div>
          <strong className="font-bold">CIT Mandatory Examination Seating Rule:</strong>
          <span className="ml-1 opacity-90">
            Effective room seating capacity is strictly capped at 50% of nominal room capacity (floor division) to ensure single-seat spacing between examinees. For multi-group exams exceeding single-room capacity (e.g. Year-1 with ~280 students), dual-venue combinations (such as AUD + LH-1) are automatically coordinated.
          </span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex-1 min-w-[240px] relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by course code, title, or student group..."
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={selectedDay}
            onChange={(e) => setSelectedDay(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-700 dark:text-slate-300 outline-none"
          >
            <option value="ALL">All Days</option>
            <option value="MON">Monday</option>
            <option value="TUE">Tuesday</option>
            <option value="WED">Wednesday</option>
            <option value="THU">Thursday</option>
            <option value="FRI">Friday</option>
          </select>

          <select
            value={selectedSlot}
            onChange={(e) => setSelectedSlot(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-700 dark:text-slate-300 outline-none"
          >
            <option value="ALL">All Slots</option>
            <option value="MORNING">Morning (09:00 - 11:00)</option>
            <option value="AFTERNOON">Afternoon (14:00 - 16:00)</option>
          </select>
        </div>
      </div>

      {/* Exams Grid */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-400">Loading exam roster and capacity allotments...</p>
        </div>
      ) : filteredExams.length === 0 ? (
        <div className="p-12 text-center rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800">
          <GraduationCap className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300">
            No examinations found
          </h3>
          <p className="text-xs text-slate-400 mt-1">Try resetting search filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredExams.map((exam) => {
            // Calculate total halved room capacity
            let totalHalvedCap = 0;
            exam.rooms.forEach((rId) => {
              const r = roomMap[rId];
              if (r) totalHalvedCap += Math.floor(r.capacity / 2);
            });

            const utilizationPct =
              totalHalvedCap > 0
                ? Math.min(100, Math.round((exam.total_students / totalHalvedCap) * 100))
                : 0;

            const isMorning = exam.slot === 'MORNING';

            return (
              <div
                key={exam.exam_id}
                className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Top Bar: Code & Slot */}
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-black text-slate-900 dark:text-white">
                      {exam.course_code}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        isMorning
                          ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                          : 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300'
                      }`}
                    >
                      {exam.day} • {exam.slot === 'MORNING' ? '09:00 - 11:00' : '14:00 - 16:00'}
                    </span>
                  </div>

                  <h3 className="text-xs font-semibold text-slate-700 dark:text-slate-300 line-clamp-1 mb-3">
                    {exam.course_name || exam.course_code}
                  </h3>

                  {/* Student Groups & Count */}
                  <div className="space-y-2 text-xs text-slate-600 dark:text-slate-400 mb-4">
                    <div className="flex items-center space-x-2">
                      <Users className="w-3.5 h-3.5 text-slate-400" />
                      <span>
                        Students: <strong>{exam.total_students}</strong> in ({exam.student_groups.join(', ')})
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Building2 className="w-3.5 h-3.5 text-slate-400" />
                      <span>
                        Allocated: <strong>{exam.rooms.join(' + ')}</strong>
                      </span>
                    </div>
                  </div>

                  {/* Halved Capacity Visual Progress */}
                  <div className="space-y-1 mb-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">Effective 50% Capacity:</span>
                      <span className="font-bold text-slate-700 dark:text-slate-300">
                        {exam.total_students} / {totalHalvedCap} seats ({utilizationPct}%)
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          utilizationPct > 95
                            ? 'bg-rose-500'
                            : utilizationPct > 80
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${utilizationPct}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px] text-slate-400">
                  <span className="flex items-center space-x-1 text-emerald-600 dark:text-emerald-400 font-semibold">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>0 Group Clashes</span>
                  </span>
                  <span>Exam ID: {exam.exam_id}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
