import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  BookOpen,
  Search,
  Filter,
  GraduationCap,
  Clock,
  Award,
  Users,
  Layers,
  ChevronDown,
  RefreshCw,
  ShieldAlert
} from 'lucide-react';

interface CourseItem {
  code: string;
  name: string;
  department: string;
  year: number;
  credits: number;
  session_types: string[];
  weekly_hours: number;
  sessions_count: number;
  instructors: string[];
  level: string;
}

export const SubjectsPage: React.FC = () => {
  const { user } = useAuth();
  const isCoordinator = user?.role === 'coordinator';
  const coordDept = (user?.department || 'CSE').toUpperCase();

  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedDept, setSelectedDept] = useState<string>(isCoordinator ? coordDept : 'ALL');
  const [selectedYear, setSelectedYear] = useState<string>('ALL');
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const data = await api.getCourses();
      setCourses(data);
    } catch (err) {
      console.error('Failed to load courses:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
    if (isCoordinator) {
      setSelectedDept(coordDept);
    }
  }, [isCoordinator, coordDept]);

  const departments = ['ALL', ...Array.from(new Set(courses.map((c) => c.department))).sort()];
  const years = ['ALL', '1', '2', '3', '4'];

  const filteredCourses = courses.filter((c) => {
    const matchesSearch =
      c.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.instructors.some((inst) => inst.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesDept = selectedDept === 'ALL' || c.department === selectedDept;
    const matchesYear = selectedYear === 'ALL' || c.year.toString() === selectedYear;
    return matchesSearch && matchesDept && matchesYear;
  });

  const totalCredits = courses.reduce((acc, c) => acc + (c.credits || 0), 0);
  const totalWeeklyHours = courses.reduce((acc, c) => acc + (c.weekly_hours || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-brand-50 dark:bg-brand-950/50 rounded-xl text-brand-600 dark:text-brand-400">
              <BookOpen className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                Subjects & Curriculum
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Complete directory of academic courses, credit allocations, syllabus hours, and assigned faculty
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchCourses}
            disabled={loading}
            className="px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-750 flex items-center space-x-1.5 transition-all shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <div className="inline-flex p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                viewMode === 'table'
                  ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Table View
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                viewMode === 'cards'
                  ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Card View
            </button>
          </div>
        </div>
      </div>

      {/* Coordinator Scope Notification */}
      {isCoordinator && (
        <div className="p-3.5 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800 flex items-center justify-between text-xs text-indigo-900 dark:text-indigo-200">
          <div className="flex items-center space-x-2 font-semibold">
            <ShieldAlert className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
            <span>🏛️ Department Coordinator View: Scoped strictly to {coordDept} subjects. Changes to courses require Dean & Administrator authorization.</span>
          </div>
          <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-indigo-200/60 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-300">
            {coordDept} Department
          </span>
        </div>
      )}

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900 dark:text-white">{courses.length}</div>
            <div className="text-[11px] font-medium text-slate-500">Total Courses</div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900 dark:text-white">
              {departments.filter((d) => d !== 'ALL').length}
            </div>
            <div className="text-[11px] font-medium text-slate-500">Academic Departments</div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900 dark:text-white">{totalCredits}</div>
            <div className="text-[11px] font-medium text-slate-500">Total Credits</div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900 dark:text-white">{totalWeeklyHours} hrs</div>
            <div className="text-[11px] font-medium text-slate-500">Weekly Scheduled Hours</div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search code (e.g. CS201), title, or instructor..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <div className="flex items-center space-x-1.5 text-xs text-slate-500">
            <Filter className="w-3.5 h-3.5" />
            <span>Dept:</span>
          </div>
          <div className="relative">
            <select
              value={selectedDept}
              disabled={isCoordinator}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="appearance-none pl-3 pr-8 py-1.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-medium focus:outline-none focus:ring-2 focus:ring-brand-500/20 disabled:opacity-80 disabled:cursor-not-allowed"
            >
              {isCoordinator ? (
                <option value={coordDept}>{coordDept} (Department Locked)</option>
              ) : (
                departments.map((d) => (
                  <option key={d} value={d}>
                    {d === 'ALL' ? 'All Departments' : d}
                  </option>
                ))
              )}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>

          <div className="flex items-center space-x-1.5 text-xs text-slate-500 ml-2">
            <GraduationCap className="w-3.5 h-3.5" />
            <span>Year:</span>
          </div>
          <div className="relative">
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              className="appearance-none pl-3 pr-8 py-1.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-medium focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            >
              {years.map((y) => (
                <option key={y} value={y}>
                  {y === 'ALL' ? 'All Years' : `Year ${y}`}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>

          {(searchTerm || selectedDept !== 'ALL' || selectedYear !== 'ALL') && (
            <button
              onClick={() => {
                setSearchTerm('');
                setSelectedDept('ALL');
                setSelectedYear('ALL');
              }}
              className="text-xs text-brand-600 dark:text-brand-400 hover:underline px-2"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Main Content: Table or Cards */}
      {loading ? (
        <div className="p-16 flex flex-col items-center justify-center text-slate-400 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800">
          <RefreshCw className="w-8 h-8 animate-spin text-brand-500 mb-3" />
          <p className="text-sm font-medium">Loading CIT subjects catalog...</p>
        </div>
      ) : filteredCourses.length === 0 ? (
        <div className="p-16 text-center bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800">
          <BookOpen className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">No courses found</h3>
          <p className="text-xs text-slate-400 mt-1">Try adjusting your search query or department filters.</p>
        </div>
      ) : viewMode === 'table' ? (
        <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-5 py-3.5">Course Code</th>
                  <th className="px-5 py-3.5">Course Name</th>
                  <th className="px-5 py-3.5">Dept & Level</th>
                  <th className="px-5 py-3.5 text-center">Credits</th>
                  <th className="px-5 py-3.5 text-center">Weekly Hours</th>
                  <th className="px-5 py-3.5">Session Types</th>
                  <th className="px-5 py-3.5">Assigned Instructors</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredCourses.map((c) => (
                  <tr
                    key={c.code}
                    className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="px-5 py-3.5 font-bold text-brand-600 dark:text-brand-400 whitespace-nowrap">
                      <span className="px-2.5 py-1 bg-brand-50 dark:bg-brand-950/60 rounded-md border border-brand-200 dark:border-brand-800">
                        {c.code}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 font-semibold text-slate-900 dark:text-slate-100">
                      {c.name}
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <span className="font-semibold text-slate-700 dark:text-slate-300">
                        {c.department}
                      </span>
                      <span className="text-slate-400 ml-1.5">• Year {c.year}</span>
                    </td>
                    <td className="px-5 py-3.5 text-center">
                      <span className="px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 font-bold text-[11px]">
                        {c.credits} CR
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-center font-bold text-slate-800 dark:text-slate-200 whitespace-nowrap">
                      {c.weekly_hours} hrs/wk
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex flex-wrap gap-1">
                        {c.session_types.map((st) => (
                          <span
                            key={st}
                            className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                              st === 'LECTURE'
                                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                                : st === 'LAB'
                                ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300'
                                : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                            }`}
                          >
                            {st}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      {c.instructors && c.instructors.length > 0 ? (
                        <div className="space-y-0.5">
                          {c.instructors.map((inst, i) => (
                            <div key={i} className="text-slate-700 dark:text-slate-300 flex items-center space-x-1.5">
                              <Users className="w-3 h-3 text-slate-400 shrink-0" />
                              <span className="truncate max-w-xs">{inst}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">Unassigned</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-5 py-3 bg-slate-50 dark:bg-slate-800/40 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <span>Showing {filteredCourses.length} of {courses.length} subjects</span>
            <span>Chilika Institute of Technology Academic Curriculum</span>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCourses.map((c) => (
            <div
              key={c.code}
              className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <span className="px-2.5 py-1 bg-brand-50 dark:bg-brand-950/60 rounded-lg border border-brand-200 dark:border-brand-800 font-bold text-brand-600 dark:text-brand-400 text-xs">
                    {c.code}
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 font-bold text-[10px]">
                    {c.credits} Credits
                  </span>
                </div>
                <h3 className="font-bold text-slate-900 dark:text-white text-sm mb-1.5 leading-snug">
                  {c.name}
                </h3>
                <div className="text-xs text-slate-500 dark:text-slate-400 mb-3 flex items-center space-x-2">
                  <span>{c.department} Dept</span>
                  <span>•</span>
                  <span>Year {c.year}</span>
                  <span>•</span>
                  <span>{c.weekly_hours} hrs/wk</span>
                </div>

                <div className="flex flex-wrap gap-1 mb-4">
                  {c.session_types.map((st) => (
                    <span
                      key={st}
                      className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                        st === 'LECTURE'
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                          : st === 'LAB'
                          ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300'
                          : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                      }`}
                    >
                      {st}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
                <div className="text-[11px] font-semibold text-slate-400 mb-1 flex items-center space-x-1">
                  <Users className="w-3 h-3" />
                  <span>Instructors</span>
                </div>
                {c.instructors.length > 0 ? (
                  <div className="space-y-0.5">
                    {c.instructors.map((inst, i) => (
                      <div key={i} className="text-xs text-slate-700 dark:text-slate-300 truncate">
                        {inst}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-slate-400 italic">None assigned</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

