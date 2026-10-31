import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { BookingRequest, Room, DayOfWeek } from '../types';
import {
  BookmarkCheck,
  Send,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Building2,
  Calendar,
  ShieldAlert,
  Mic
} from 'lucide-react';

const DAYS: DayOfWeek[] = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
const PERIODS = [1, 2, 3, 4, 5, 6, 7, 8, 9];

export const BookingsPage: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();

  const [bookings, setBookings] = useState<BookingRequest[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);

  // Form tab: 'structured' vs 'natural'
  const [activeTab, setActiveTab] = useState<'structured' | 'natural'>('structured');

  // Form Fields
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('ACADEMIC');
  const [requestedRoom, setRequestedRoom] = useState('LH-1');
  const [day, setDay] = useState<DayOfWeek>('THU');
  const [startPeriod, setStartPeriod] = useState<number>(6);
  const [duration, setDuration] = useState<number>(2);
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Natural language input
  const [promptInput, setPromptInput] = useState('');
  const [parsing, setParsing] = useState(false);

  // Rejection modal
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  // Prefill from Find Room page if navigated from there
  useEffect(() => {
    if (location.state) {
      const { prefillRoom, prefillDay, prefillPeriod, prefillDuration } = location.state as any;
      if (prefillRoom) setRequestedRoom(prefillRoom);
      if (prefillDay) setDay(prefillDay);
      if (prefillPeriod) setStartPeriod(prefillPeriod);
      if (prefillDuration) setDuration(prefillDuration);
    }
  }, [location.state]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [bList, rList] = await Promise.all([
        api.getBookings(),
        api.getRooms(),
      ]);
      setBookings(bList);
      setRooms(rList);
      if (rList.length > 0 && !location.state?.prefillRoom) {
        setRequestedRoom(rList[0].room_id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateStructured = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      await api.createBooking({
        title,
        category,
        requested_room: requestedRoom,
        day,
        start_period: startPeriod,
        duration,
        requester_name: user?.name || 'Faculty Member',
        requester_email: user?.email || 'faculty@cit.edu',
        requester_role: user?.role || 'faculty',
      });
      setActionSuccess('Booking request registered! Evaluated by CP-SAT solver.');
      setTitle('');
      await loadData();
    } catch (err: any) {
      setActionError(err.message || 'Failed to submit booking');
    } finally {
      setSubmitting(false);
    }
  };

  const handleParseNatural = async () => {
    if (!promptInput.trim()) return;
    setParsing(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      const proposal = await api.askAssistant(promptInput);
      if (proposal && proposal.parsed) {
        const p = proposal.parsed;
        if (p.requested_room || p.room_id) setRequestedRoom(p.requested_room || p.room_id);
        if (p.day) setDay(p.day);
        if (p.start_period) setStartPeriod(p.start_period);
        if (p.duration) setDuration(p.duration);
        if (p.title) setTitle(p.title);
        else setTitle(promptInput);

        setActiveTab('structured');
        setActionSuccess(`Natural language parsed! Feasible: ${proposal.feasible ? 'Yes' : 'No'}. ${proposal.explanation}`);
      }
    } catch (err: any) {
      setActionError(err.message || 'Failed to parse natural language prompt');
    } finally {
      setParsing(false);
    }
  };

  const handleApprove = async (booking: BookingRequest) => {
    if (user && booking.requester_email === user.email) {
      setActionError('Strict Security Policy: You cannot approve your own booking request.');
      return;
    }

    try {
      await api.approveBooking(booking.request_id);
      await loadData();
      setActionSuccess(`Request ${booking.request_id} approved.`);
    } catch (err: any) {
      setActionError(err.message || 'Approval failed');
    }
  };

  const handleRejectConfirm = async () => {
    if (!rejectingId) return;
    try {
      await api.rejectBooking(rejectingId, rejectReason || 'Slot unavailable due to academic priority');
      setRejectingId(null);
      setRejectReason('');
      await loadData();
      setActionSuccess('Booking rejected with reason.');
    } catch (err: any) {
      setActionError(err.message || 'Rejection failed');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Title */}
      <div>
        <div className="flex items-center space-x-2">
          <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
            Venue Booking Hub
          </h1>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-brand-100 text-brand-800 dark:bg-brand-950/60 dark:text-brand-300">
            Multi-Tier Priority
          </span>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Reserve auditoriums, seminar halls, and lecture halls with automated conflict detection and strict anti-self-approval security.
        </p>
      </div>

      {/* Alerts */}
      {actionError && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {actionSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Submission Card with Two Tabs */}
      <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-4 border-b border-slate-100 dark:border-slate-800 pb-3">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setActiveTab('structured')}
              className={`text-xs font-bold pb-1 transition-all border-b-2 ${
                activeTab === 'structured'
                  ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                  : 'border-transparent text-slate-400 hover:text-slate-600'
              }`}
            >
              Standard Form
            </button>
            <button
              onClick={() => setActiveTab('natural')}
              className={`text-xs font-bold pb-1 transition-all border-b-2 flex items-center space-x-1 ${
                activeTab === 'natural'
                  ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                  : 'border-transparent text-slate-400 hover:text-slate-600'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Voice / Hinglish Prompt</span>
            </button>
          </div>
        </div>

        {activeTab === 'natural' ? (
          <div className="space-y-4">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Type or paste your booking request in natural English or conversational Hinglish (e.g. <em>"LH-1 chahiye Thursday 2 baje for Robotics workshop"</em>).
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={promptInput}
                onChange={(e) => setPromptInput(e.target.value)}
                placeholder="LH-1 chahiye Thursday 2 baje for 2 hours Robotics meet..."
                className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-brand-500"
              />
              <button
                onClick={handleParseNatural}
                disabled={parsing || !promptInput.trim()}
                className="px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors disabled:opacity-50"
              >
                {parsing ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Parse & Populate</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleCreateStructured} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="lg:col-span-2">
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Event / Session Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. AI Guest Lecture / Robotics Workshop"
                  required
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none"
                >
                  <option value="ACADEMIC">Academic / Workshop</option>
                  <option value="CLUB">Student Club Activity</option>
                  <option value="SPECTRA">Spectra Fest Event</option>
                  <option value="MAINTENANCE">Maintenance</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Requested Venue
                </label>
                <select
                  value={requestedRoom}
                  onChange={(e) => setRequestedRoom(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none"
                >
                  {rooms.map((r) => (
                    <option key={r.room_id} value={r.room_id}>
                      {r.name || r.room_id} ({r.type} - Cap: {r.capacity})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Day
                </label>
                <select
                  value={day}
                  onChange={(e) => setDay(e.target.value as DayOfWeek)}
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
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Start Period
                </label>
                <select
                  value={startPeriod}
                  onChange={(e) => setStartPeriod(Number(e.target.value))}
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
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Duration
                </label>
                <select
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none"
                >
                  <option value={1}>1 Period (1 hr)</option>
                  <option value={2}>2 Periods (2 hrs)</option>
                  <option value={3}>3 Periods (3 hrs)</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs transition-colors flex items-center justify-center space-x-1.5 shadow-md shadow-brand-500/20 disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Request</span>
                </button>
              </div>
            </div>
          </form>
        )}
      </div>

      {/* Bookings Queue */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            Active Requests & Approvals Queue ({bookings.length})
          </h2>
          <span className="text-xs text-slate-400">
            Requester cannot self-approve
          </span>
        </div>

        {loading ? (
          <div className="py-12 flex justify-center">
            <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : bookings.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-xs text-slate-400">
            No booking requests registered.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {bookings.map((b) => {
              const isOwnRequest = user && b.requester_email === user.email;
              const canModerate = user && (user.role === 'admin' || user.role === 'coordinator');

              return (
                <div
                  key={b.request_id}
                  className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold text-slate-900 dark:text-white">
                        {b.title}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          b.status === 'APPROVED'
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                            : b.status === 'ALTERNATIVE_OFFERED'
                            ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300'
                            : b.status === 'REJECTED'
                            ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
                            : 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                        }`}
                      >
                        {b.status}
                      </span>
                    </div>

                    <div className="space-y-1.5 text-xs text-slate-500 dark:text-slate-400 mb-3">
                      <div>
                        Requester: <strong>{b.requester_name}</strong> ({b.requester_email})
                      </div>
                      <div>
                        Slot: <strong>{b.day} Period {b.start_period}</strong> ({b.duration} hrs) • Requested Venue: <strong>{b.requested_room}</strong>
                      </div>
                      {b.reason && (
                        <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-950/60 border border-slate-200/50 dark:border-slate-800 text-[11px] text-slate-600 dark:text-slate-300">
                          {b.reason}
                        </div>
                      )}
                    </div>

                    {/* Alternatives if offered */}
                    {b.alternatives && b.alternatives.length > 0 && (
                      <div className="mb-3 p-2 rounded-xl bg-blue-50/50 dark:bg-blue-950/30 border border-blue-200/50 dark:border-blue-900 text-xs">
                        <span className="font-semibold text-blue-700 dark:text-blue-300 block mb-1">
                          Alternative Slots Available:
                        </span>
                        <div className="space-y-1">
                          {b.alternatives.map((alt, idx) => (
                            <div key={idx} className="text-[11px] text-blue-600 dark:text-blue-400">
                              • {alt.room_id} on {alt.day} (Period {alt.start_period})
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Actions Bar */}
                  <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                    <span className="text-[10px] text-slate-400">{b.request_id}</span>

                    {b.status === 'PENDING' && canModerate && (
                      <div className="flex items-center space-x-2">
                        {isOwnRequest ? (
                          <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50 px-2 py-1 rounded-md flex items-center space-x-1">
                            <ShieldAlert className="w-3 h-3" />
                            <span>Cannot approve own request</span>
                          </span>
                        ) : (
                          <>
                            <button
                              onClick={() => handleApprove(b)}
                              className="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-semibold transition-colors"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => setRejectingId(b.request_id)}
                              className="px-2.5 py-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-[11px] font-semibold transition-colors"
                            >
                              Reject
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Rejection Modal */}
      {rejectingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Reject Booking Request
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Please state the specific reason for rejecting request {rejectingId} (e.g. priority clash, capacity violation).
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Main Auditorium reserved for academic midsem exams..."
              rows={3}
              className="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-rose-500"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setRejectingId(null)}
                className="px-3 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectConfirm}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 text-white hover:bg-rose-700 transition-colors"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
