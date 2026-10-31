from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from app.db import db_manager
from app.scheduler.dataset_adapter import load_default_dataset, PERIOD_INDEX, PERIODS, TEACHING_PERIODS, DAYS
from app.scheduler.candidates import is_room_type_compatible

router = APIRouter(prefix="/views", tags=["Views"])

@router.get("/timetable")
def get_filtered_timetable(
    group_id: Optional[str] = Query(None),
    faculty_id: Optional[str] = Query(None),
    room_id: Optional[str] = Query(None),
    version: Optional[int] = Query(None)
):
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")

    if version:
        t = timetables_col.find_one({"version": version})
    else:
        state = state_col.find_one({"_id": "state"})
        pub_ver = state.get("published_version") if state else None
        if pub_ver:
            t = timetables_col.find_one({"version": pub_ver})
        else:
            latest = timetables_col.find().sort("version", -1).limit(1).to_list()
            t = latest[0] if latest else None

    ds = load_default_dataset()
    assignments = t.get("assignments", []) if t else []
    version_num = t.get("version") if t else 1

    if not assignments:
        import os, json
        schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
        if os.path.exists(schedule_path):
            try:
                with open(schedule_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    assignments = data.get("timetable", [])
                    version_num = 1
            except Exception:
                pass

    if not assignments:
        return {"version": None, "slots": []}
    filtered_slots = []

    for a in assignments:
        sid = a["session_id"]
        s = ds.sessions_by_id.get(sid)
        if not s:
            continue

        # Filters
        if group_id and group_id not in s.student_groups:
            continue
        if faculty_id and faculty_id not in s.faculty_ids:
            continue
        if room_id and a["room_id"] != room_id:
            continue

        room = ds.rooms_by_id.get(a["room_id"])
        c = ds.courses_by_code.get(s.course_code)

        filtered_slots.append({
            "session_id": sid,
            "course_code": s.course_code,
            "course_name": c.name if c else s.course_code,
            "session_type": s.session_type,
            "duration_hours": s.duration_hours,
            "day": a["day"],
            "start_period": a["start_period"],
            "room_id": a["room_id"],
            "room_name": room.name if room else a["room_id"],
            "faculty_ids": s.faculty_ids,
            "faculty_names": [ds.faculty_by_id[fid].name for fid in s.faculty_ids if fid in ds.faculty_by_id],
            "student_groups": s.student_groups,
            "elective_basket": s.elective_basket,
            "is_fixed": bool(s.fixed_slot)
        })

    return {
        "version": t.get("version"),
        "total_sessions": len(filtered_slots),
        "slots": filtered_slots
    }

def check_room_type_match(selected_type: Optional[str], room_type: str) -> bool:
    if not selected_type or selected_type.upper() in ("ALL", "ANY"):
        return True
    sel = selected_type.lower()
    rt = room_type.lower()
    if sel in ("classroom", "classrooms"):
        return rt in ("classroom", "lecture_hall", "tutorial_room")
    if sel in ("lab", "laboratories", "labs"):
        return "lab" in rt
    if sel in ("auditorium", "auditoriums"):
        return "auditorium" in rt or "theatre" in rt or "oat" in rt
    if sel in ("seminar_hall", "seminar", "seminar_halls"):
        return "seminar" in rt
    if sel in ("lecture_hall", "lecture_halls"):
        return "lecture" in rt or "auditorium" in rt or "classroom" in rt
    return sel in rt or rt in sel

@router.get("/free-rooms")
def find_free_rooms(
    day: str = Query(..., description="Mon | Tue | Wed | Thu | Fri or MON | TUE..."),
    period: Optional[str] = Query(None, description="P1 through P13"),
    start_period: Optional[Any] = Query(None, description="Period number (1-9) or P1-P9"),
    duration_hours: int = Query(1, ge=1, le=4),
    duration: Optional[int] = Query(None),
    capacity: int = Query(0, ge=0),
    min_capacity: Optional[int] = Query(None),
    room_type: Optional[str] = Query(None)
):
    ds = load_default_dataset()
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")

    # Normalize day
    day_norm = day.capitalize()[:3] if day else "Mon"

    # Normalize period / start_period
    eff_period = period
    if not eff_period and start_period is not None:
        sp_str = str(start_period).strip().upper()
        eff_period = sp_str if sp_str.startswith("P") else f"P{sp_str}"
    if not eff_period:
        eff_period = "P1"

    eff_duration = duration if duration is not None else duration_hours
    eff_capacity = min_capacity if min_capacity is not None else capacity
    eff_room_type = None if (room_type in (None, "", "undefined", "ALL", "null")) else room_type

    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None
    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else None

    # Calculate periods to check
    start_idx = PERIOD_INDEX.get(eff_period, 0)
    covered = [PERIODS[start_idx + i] for i in range(eff_duration) if start_idx + i < len(PERIODS)]

    # Occupied rooms from timetable
    occupied_rooms = set()
    t_assignments = t.get("assignments", []) if t else []
    if not t_assignments:
        import os, json
        schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
        if os.path.exists(schedule_path):
            try:
                with open(schedule_path, "r", encoding="utf-8") as f:
                    t_assignments = json.load(f).get("timetable", [])
            except Exception:
                pass

    for a in t_assignments:
        if a["day"] == day_norm:
            s = ds.sessions_by_id.get(a["session_id"])
            dur = s.duration_hours if s else 1
            s_i = PERIOD_INDEX.get(a["start_period"], 0)
            a_cov = [PERIODS[s_i + j] for j in range(dur) if s_i + j < len(PERIODS)]
            if any(p in covered for p in a_cov):
                occupied_rooms.add(a["room_id"])

    # Occupied rooms from approved bookings
    bookings_col = db_manager.get_collection("bookings")
    for b in bookings_col.find({"status": "approved", "day": day_norm}):
        b_room = b.get("assigned_room")
        if b_room:
            b_s = PERIOD_INDEX.get(b.get("start_period"), 0)
            b_e = PERIOD_INDEX.get(b.get("end_period"), b_s)
            b_cov = [PERIODS[k] for k in range(b_s, b_e + 1) if k < len(PERIODS)]
            if any(p in covered for p in b_cov):
                occupied_rooms.add(b_room)

    free_rooms = []
    frontend_rooms = []
    for r in ds.rooms:
        if r.id in occupied_rooms:
            continue
        if eff_capacity > 0 and r.capacity < eff_capacity:
            continue
        if eff_room_type and not check_room_type_match(eff_room_type, r.type):
            continue

        # Check maintenance
        under_maint = False
        for m in r.maintenance_windows:
            if m.get("day") == day_norm:
                ms = PERIOD_INDEX.get(m.get("start_period"), -1)
                me = PERIOD_INDEX.get(m.get("end_period"), -1)
                if any(ms <= PERIOD_INDEX.get(p, -1) <= me for p in covered):
                    under_maint = True
                    break
        if under_maint:
            continue

        rtype = "CLASSROOM"
        t_low = r.type.lower()
        if "lab" in t_low:
            rtype = "LAB"
        elif "auditorium" in t_low or "oat" in t_low or "theatre" in t_low:
            rtype = "AUDITORIUM"
        elif "seminar" in t_low:
            rtype = "SEMINAR_HALL"

        room_dict = {
            "id": r.id,
            "room_id": r.id,
            "name": r.name,
            "building": "Central Complex" if ("aud" in r.id.lower() or "oat" in r.id.lower()) else "Academic Block",
            "floor": 1 if any(c in r.id for c in ["1", "A"]) else 2,
            "type": rtype,
            "capacity": r.capacity,
            "accessible": r.accessible,
            "features": r.features or ["PROJECTOR", "AC", "WHITEBOARD"],
            "is_active": True
        }
        free_rooms.append(room_dict)
        frontend_rooms.append(room_dict)

    return {
        "day": day_norm,
        "period": eff_period,
        "duration_hours": eff_duration,
        "covered_periods": covered,
        "free_rooms_count": len(free_rooms),
        "total_checked": len(ds.rooms),
        "rooms": free_rooms,
        "available_rooms": frontend_rooms
    }
