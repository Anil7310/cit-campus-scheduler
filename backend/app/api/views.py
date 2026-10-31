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

    if not t:
        return {"version": None, "slots": []}

    ds = load_default_dataset()
    assignments = t.get("assignments", [])
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

@router.get("/free-rooms")
def find_free_rooms(
    day: str = Query(..., description="Mon | Tue | Wed | Thu | Fri"),
    period: str = Query(..., description="P1 through P13"),
    duration_hours: int = Query(1, ge=1, le=4),
    capacity: int = Query(0, ge=0),
    room_type: Optional[str] = Query(None)
):
    ds = load_default_dataset()
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")

    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None
    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else None

    # Calculate periods to check
    start_idx = PERIOD_INDEX.get(period, 0)
    covered = [PERIODS[start_idx + i] for i in range(duration_hours) if start_idx + i < len(PERIODS)]

    # Occupied rooms from timetable
    occupied_rooms = set()
    if t:
        for a in t.get("assignments", []):
            if a["day"] == day:
                s = ds.sessions_by_id.get(a["session_id"])
                dur = s.duration_hours if s else 1
                s_i = PERIOD_INDEX.get(a["start_period"], 0)
                a_cov = [PERIODS[s_i + j] for j in range(dur) if s_i + j < len(PERIODS)]
                if any(p in covered for p in a_cov):
                    occupied_rooms.add(a["room_id"])

    # Occupied rooms from approved bookings
    bookings_col = db_manager.get_collection("bookings")
    for b in bookings_col.find({"status": "approved", "day": day}):
        b_room = b.get("assigned_room")
        if b_room:
            b_s = PERIOD_INDEX.get(b.get("start_period"), 0)
            b_e = PERIOD_INDEX.get(b.get("end_period"), b_s)
            b_cov = [PERIODS[k] for k in range(b_s, b_e + 1) if k < len(PERIODS)]
            if any(p in covered for p in b_cov):
                occupied_rooms.add(b_room)

    free_rooms = []
    for r in ds.rooms:
        if r.id in occupied_rooms:
            continue
        if capacity > 0 and r.capacity < capacity:
            continue
        if room_type and not is_room_type_compatible(room_type, r.type):
            continue

        # Check maintenance
        under_maint = False
        for m in r.maintenance_windows:
            if m.get("day") == day:
                ms = PERIOD_INDEX.get(m.get("start_period"), -1)
                me = PERIOD_INDEX.get(m.get("end_period"), -1)
                if any(ms <= PERIOD_INDEX.get(p, -1) <= me for p in covered):
                    under_maint = True
                    break
        if under_maint:
            continue

        free_rooms.append({
            "id": r.id,
            "name": r.name,
            "type": r.type,
            "capacity": r.capacity,
            "accessible": r.accessible,
            "features": r.features
        })

    return {
        "day": day,
        "period": period,
        "duration_hours": duration_hours,
        "covered_periods": covered,
        "free_rooms_count": len(free_rooms),
        "rooms": free_rooms
    }
