import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Room, DayOfWeek } from '../types';
import {
  Search,
  Building2,
  Users,
  Clock,
  Sparkles,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';

const DAYS: DayOfWeek[] = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
const PERIODS = [1, 2, 3, 4, 5, 6, 7, 8, 9];

const PERIOD_TIMES: Record<number, string> = {
  1: 'P1 (08:00 - 09:00)',
  2: 'P2 (09:00 - 10:00)',
  3: 'P3 (10:00 - 11:00)',
  4: 'P4 (11:00 - 12:00)',
  5: 'P5 (12:00 - 13:00)',
  6: 'P6 (13:00 - 14:00)',
  7: 'P7 (14:00 - 15:00)',
  8: 'P8 (15:00 - 16:00)',
  9: 'P9 (16:00 - 17:00)',
};

export const FindRoomPage: React.FC = () => {
  const navigate = useNavigate();

  const [day, setDay] = useState<DayOfWeek>('MON');
  const [startPeriod, setStartPeriod] = useState<number>(3);
  const [duration, setDuration] = useState<number>(1);
  const [minCapacity, setMinCapacity] = useState<number>(40);
  const [roomType, setRoomType] = useState<string>('ALL');

  const [availableRooms, setAvailableRooms] = useState<Room[]>([]);
  const [totalChecked, setTotalChecked] = useState<number>(27);
  const [loading, setLoading] = useState(false);

  const searchFreeRooms = async () => {
    setLoading(true);
    try {
      const res = await api.findFreeRooms({
        day,
        start_period: startPeriod,
        duration,
        min_capacity: minCapacity,
        room_type: roomType !== 'ALL' ? roomType : undefined,
      });
      setAvailableRooms(res.available_rooms || []);
      setTotalChecked(res.total_checked || 27);
    } catch (e) {
      console.error('Error finding rooms', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    searchFreeRooms();
  }, [day, startPeriod, duration, minCapacity, roomType]);

  const handleBook = (room: Room) => {
    navigate('/bookings', {
      state: {
        prefillRoom: room.room_id,
        prefillDay: day,
        prefillPeriod: startPeriod,
        prefillDuration: duration,
      },
    });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Title */}
      <div>
        <div className="flex items-center space-x-2">
          <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
            Instant Free Room Finder
          </h1>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
            Real-Time Vacancy
          </span>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Detect vacant lecture halls, labs, and auditoriums clash-checked against the active semester schedule.
        </p>
      </div>

      {/* Query Filter Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Day */}
          <div>
            <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 mb-1.5">
              Day of Week
            </label>
            <select
              value={day}
              onChange={(e) => setDay(e.target.value as DayOfWeek)}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-brand-500"
            >
              {DAYS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          {/* Start Period */}
          <div>
            <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 mb-1.5">
              Start Period
            </label>
            <select
              value={startPeriod}
              onChange={(e) => setStartPeriod(Number(e.target.value))}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-brand-500"
            >
              {PERIODS.map((p) => (
                <option key={p} value={p}>
                  {PERIOD_TIMES[p]}
                </option>
              ))}
            </select>
          </div>

          {/* Duration */}
          <div>
            <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 mb-1.5">
              Duration
            </label>
            <select
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value={1}>1 Period (1 Hour)</option>
              <option value={2}>2 Periods (2 Hours Continuous)</option>
              <option value={3}>3 Periods (3 Hours Continuous)</option>
            </select>
          </div>

          {/* Room Type */}
          <div>
            <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 mb-1.5">
              Venue Type
            </label>
            <select
              value={roomType}
              onChange={(e) => setRoomType(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="ALL">All Categories</option>
              <option value="CLASSROOM">Classrooms</option>
              <option value="LAB">Laboratories</option>
              <option value="AUDITORIUM">Auditoriums</option>
              <option value="SEMINAR_HALL">Seminar Halls</option>
            </select>
          </div>

          {/* Min Capacity */}
          <div>
            <label className="block text-xs font-bold text-slate-600 dark:text-slate-400 mb-1.5">
              Min Capacity: <span className="text-brand-600 dark:text-brand-400">{minCapacity} seats</span>
            </label>
            <input
              type="range"
              min={20}
              max={300}
              step={10}
              value={minCapacity}
              onChange={(e) => setMinCapacity(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-brand-600 mt-3"
            />
          </div>
        </div>

        {/* Counter Summary */}
        <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            <span>
              Found <strong className="text-slate-900 dark:text-white">{availableRooms.length}</strong> available venues out of {totalChecked} total campus rooms.
            </span>
          </div>

          {startPeriod <= 5 && startPeriod + duration - 1 >= 5 && (
            <span className="text-[11px] text-amber-600 dark:text-amber-400 font-semibold bg-amber-50 dark:bg-amber-950/50 px-2 py-0.5 rounded-md">
              Note: Slot overlaps with standard CIT lunch hour (P5: 12-1 PM).
            </span>
          )}
        </div>
      </div>

      {/* Available Rooms Grid */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-400">Scanning campus occupancy schedule...</p>
        </div>
      ) : availableRooms.length === 0 ? (
        <div className="p-12 text-center rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800">
          <Building2 className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300">
            No vacant venues match these criteria
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Try adjusting the period, lowering the minimum capacity, or selecting another day.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {availableRooms.map((room) => (
            <div
              key={room.room_id}
              className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md hover:border-brand-500/40 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-base font-extrabold text-slate-900 dark:text-white">
                    {room.name || room.room_id}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    {room.type}
                  </span>
                </div>

                <div className="space-y-1.5 text-xs text-slate-500 dark:text-slate-400 mb-4">
                  <div className="flex items-center space-x-2">
                    <Building2 className="w-3.5 h-3.5 text-slate-400" />
                    <span>
                      {room.building} • Floor {room.floor}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                    <span>Capacity: <strong>{room.capacity} seats</strong></span>
                  </div>
                </div>

                {/* Features tags */}
                {room.features && room.features.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-4">
                    {room.features.map((feat, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-indigo-950/40 text-brand-700 dark:text-brand-300"
                      >
                        {feat}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <button
                onClick={() => handleBook(room)}
                className="w-full py-2 px-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-brand-600 hover:text-white text-slate-800 dark:text-slate-200 text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 group"
              >
                <span>Book This Room</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
