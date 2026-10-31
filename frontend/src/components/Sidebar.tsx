import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  CalendarDays,
  Search,
  GraduationCap,
  Sparkles,
  Layers,
  Bot,
  Sliders,
  FileSpreadsheet,
  Settings,
  X,
  Compass,
  BookmarkCheck,
  BookOpen,
  UserCheck
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const role = user?.role || 'admin';

  // Role-specific navigation separation
  const getNavGroups = () => {
    if (role === 'faculty') {
      return [
        {
          title: 'Faculty Workspace',
          items: [
            { to: '/faculty', label: 'My Faculty Portal', icon: UserCheck },
            { to: '/timetable', label: 'Master Timetable', icon: CalendarDays },
            { to: '/find-room', label: 'Instant Free Room', icon: Search },
            { to: '/assistant', label: 'AI Voice & Hinglish', icon: Bot },
          ],
        },
      ];
    }

    if (role === 'club') {
      return [
        {
          title: 'Student Club Operations',
          items: [
            { to: '/spectra', label: 'Spectra 2026 Fest', icon: Sparkles },
            { to: '/bookings', label: 'Venue Bookings', icon: BookmarkCheck },
            { to: '/find-room', label: 'Instant Free Room', icon: Search },
            { to: '/assistant', label: 'AI Voice & Hinglish', icon: Bot },
          ],
        },
      ];
    }

    if (role === 'coordinator') {
      return [
        {
          title: 'Academic Coordination',
          items: [
            { to: '/', label: 'Dashboard', icon: LayoutDashboard },
            { to: '/timetable', label: 'Master Timetable', icon: CalendarDays },
            { to: '/subjects', label: 'Subjects Directory', icon: BookOpen },
            { to: '/find-room', label: 'Instant Free Room', icon: Search },
          ],
        },
        {
          title: 'Operations & Solver',
          items: [
            { to: '/bookings', label: 'Venue Bookings', icon: BookmarkCheck },
            { to: '/reschedule', label: 'Rescheduling Engine', icon: Layers },
            { to: '/exams', label: 'Midsem Exams', icon: GraduationCap },
            { to: '/assistant', label: 'AI Voice & Hinglish', icon: Bot },
          ],
        },
      ];
    }

    // Default / Admin
    return [
      {
        title: 'Administration',
        items: [
          { to: '/', label: 'Dashboard', icon: LayoutDashboard },
          { to: '/subjects', label: 'Subjects & Curriculum', icon: BookOpen },
          { to: '/timetable', label: 'Master Timetable', icon: CalendarDays },
          { to: '/exams', label: 'Midsem Exams', icon: GraduationCap },
        ],
      },
      {
        title: 'Venues & Solver Engine',
        items: [
          { to: '/bookings', label: 'Venue Bookings', icon: BookmarkCheck },
          { to: '/reschedule', label: 'Rescheduling Engine', icon: Layers },
          { to: '/manual', label: 'Manual Placement', icon: Sliders },
          { to: '/find-room', label: 'Instant Free Room', icon: Search },
        ],
      },
      {
        title: 'System & Tools',
        items: [
          { to: '/import', label: 'Dataset & Solvers', icon: FileSpreadsheet },
          { to: '/settings', label: 'Settings & Audit', icon: Settings },
          { to: '/assistant', label: 'AI Voice & Hinglish', icon: Bot },
        ],
      },
    ];
  };

  const navGroups = getNavGroups();

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden transition-opacity"
        />
      )}

      {/* Sidebar Content */}
      <aside
        className={`fixed top-0 left-0 bottom-0 z-40 w-64 bg-white/90 dark:bg-slate-900/95 backdrop-blur-xl border-r border-slate-200/80 dark:border-slate-800 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Logo Header */}
        <div className="h-16 px-6 flex items-center justify-between border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-3">
            <img
              src="/logo.jpg"
              alt="CIT Logo"
              className="w-10 h-10 rounded-full object-cover shadow-sm ring-2 ring-brand-500/30 bg-white"
            />
            <div>
              <span className="text-base font-extrabold tracking-tight bg-gradient-to-r from-slate-900 via-indigo-900 to-brand-700 dark:from-white dark:via-slate-200 dark:to-indigo-300 bg-clip-text text-transparent">
                CIT TTMS
              </span>
              <span className="block text-[10px] text-slate-400 font-semibold tracking-wider uppercase">
                Chilika Institute
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Groups */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
          {navGroups.map((group, idx) => (
            <div key={idx} className="space-y-1">
              <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                {group.title}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => {
                      if (window.innerWidth < 1024) onClose();
                    }}
                    className={({ isActive }) =>
                      `flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-brand-500/10 dark:bg-brand-500/20 text-brand-600 dark:text-brand-300 font-semibold shadow-sm'
                          : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </div>
          ))}
        </div>

        {/* User Card at Bottom */}
        {user && (
          <div className="p-4 border-t border-slate-100 dark:border-slate-800">
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/50 dark:border-slate-700/40 flex items-center space-x-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold">
                {user.name.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                  {user.name}
                </p>
                <p className="text-[10px] text-slate-400 truncate uppercase tracking-wider">
                  {user.role} {user.department ? `• ${user.department}` : ''}
                </p>
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
};
