import logging
import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.security import get_current_user
from app.db import db_manager
from app.scheduler.dataset_adapter import load_default_dataset, PERIOD_INDEX, PERIODS

logger = logging.getLogger("cit_scheduler.faculty_api")
router = APIRouter(prefix="/faculty", tags=["Faculty Portal"])

PERIOD_TIMES = {
    1: "08:00 - 09:00",
    2: "09:00 - 10:00",
    3: "10:00 - 11:00",
    4: "11:00 - 12:00",
    5: "12:00 - 13:00 (Lunch)",
    6: "13:00 - 14:00",
    7: "14:00 - 15:00",
    8: "15:00 - 16:00",
    9: "16:00 - 17:00"
}

# In-memory store for faculty lecture modifications and weekend requests
_faculty_actions_store = []
_weekend_requests_store = []

# Mock rich faculty metadata (qualifications, interests)
FACULTY_PROFILES = {
    "F01": {
        "id": "F01",
        "name": "Dr. A. Sharma",
        "designation": "Associate Professor & Head of Distributed Systems Lab",
        "department": "Computer Science & Engineering",
        "email": "faculty@cit.edu",
        "phone": "+91 94370 12345",
        "cabin": "CSB-204, Academic Block",
        "qualifications": [
            "Ph.D. in Computer Science (IIT Kharagpur, 2016)",
            "M.Tech in Software Systems (NIT Rourkela, 2010)",
            "B.Tech in Computer Science & Engineering (First Class with Distinction)"
        ],
        "fields_of_interest": [
            "Distributed Systems & Cloud Computing",
            "Integer Programming & Exact Mathematical Optimization",
            "High Performance Parallel Algorithms",
            "Modern Operating Systems Architecture"
        ],
        "teaching_subjects": [
            {"code": "CS102", "name": "Programming Lab", "groups": ["Y1-A"], "weekly_hours": 3, "room": "LAB-CS2"},
            {"code": "CS305A", "name": "Machine Learning (Elective)", "groups": ["Y3-CSE"], "weekly_hours": 3, "room": "LH-2"}
        ],
        "planned_weekly_hours": 6,
        "max_daily_hours": 4
    }
}

def _get_faculty_profile(faculty_id: str, current_user: dict):
    fid = faculty_id or "F01"
    if fid in FACULTY_PROFILES:
        return FACULTY_PROFILES[fid]
    
    users_col = db_manager.get_collection("users")
    u = users_col.find_one({"$or": [{"faculty_id": fid}, {"username": fid}, {"email": fid}]})
    if u:
        prof = {
            "id": u.get("faculty_id") or fid,
            "name": u.get("name"),
            "designation": "Assistant Professor",
            "department": u.get("department", "Engineering"),
            "email": u.get("email"),
            "phone": "+91 94370 88990",
            "cabin": f"{u.get('department', 'Academic')}-Block, Cabin 104",
            "qualifications": u.get("qualifications") or [
                "Ph.D. in Engineering (Premier Institute)",
                "M.Tech / M.E.",
                "B.Tech / B.E."
            ],
            "fields_of_interest": u.get("fields_of_interest") or [
                "Advanced Research & Development",
                "Distributed Algorithms"
            ],
            "teaching_subjects": [],
            "planned_weekly_hours": 6,
            "max_daily_hours": 4
        }
        FACULTY_PROFILES[fid] = prof
        return prof

    ds = load_default_dataset()
    f_obj = ds.faculty_by_id.get(fid)
    name = f_obj.name if f_obj else current_user.get("name", "Faculty Member")
    dept = f_obj.department if f_obj else "Engineering"

    return {
        "id": fid,
        "name": name,
        "designation": "Assistant Professor",
        "department": dept,
        "email": current_user.get("email", f"{fid.lower()}@cit.edu"),
        "phone": "+91 94370 00000",
        "cabin": "Faculty Wing, Academic Block",
        "qualifications": [
            "Ph.D. in Engineering (Premier Institute)",
            "M.Tech / M.E. in Specialized Engineering Discipline",
            "B.Tech / B.E. (Honors)"
        ],
        "fields_of_interest": [
            "Advanced Pedagogy & Engineering Research",
            "Computational Modeling & Simulation",
            "Applied Data Analysis"
        ],
        "teaching_subjects": [],
        "planned_weekly_hours": 4,
        "max_daily_hours": 4
    }

@router.get("/profile")
def get_faculty_profile(current_user: dict = Depends(get_current_user)):
    fid = current_user.get("faculty_id") or "F01"
    return _get_faculty_profile(fid, current_user)

@router.get("/my-schedule")
def get_faculty_schedule(current_user: dict = Depends(get_current_user)):
    fid = current_user.get("faculty_id") or "F01"
    ds = load_default_dataset()

    # Load baseline schedule
    schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
    assignments = []
    if os.path.exists(schedule_path):
        with open(schedule_path, "r", encoding="utf-8") as f:
            assignments = json.load(f).get("timetable", [])

    # Filter for this faculty's sessions
    my_sessions = []
    for a in assignments:
        s = ds.sessions_by_id.get(a["session_id"])
        if not s or fid not in s.faculty_ids:
            continue

        c = ds.courses_by_code.get(s.course_code)
        cname = c.name if c else s.course_code
        sp_int = int(str(a["start_period"]).replace("P", ""))
        dur = s.duration_hours

        # Check if modified by faculty
        action_match = next((act for act in _faculty_actions_store if act["session_id"] == a["session_id"]), None)
        status_label = "ACTIVE"
        note = None
        if action_match:
            act_stat = action_match.get("status", "PENDING")
            if act_stat == "APPROVED":
                status_label = action_match["action_type"]
                note = action_match.get("reason")
            elif act_stat == "REJECTED":
                status_label = "ACTIVE"
                note = f"Modification request rejected by Admin: {action_match.get('reason', '')}"
            else:
                status_label = f"PENDING_{action_match['action_type']}"
                note = f"Pending Admin Approval: {action_match.get('reason', '')}"

        my_sessions.append({
            "session_id": a["session_id"],
            "course_code": s.course_code,
            "course_name": cname,
            "session_type": s.session_type.upper(),
            "group_id": s.student_groups[0] if s.student_groups else "Y1-A",
            "student_groups": s.student_groups,
            "room_id": a["room_id"],
            "day": a["day"].upper()[:3],
            "start_period": sp_int,
            "duration": dur,
            "time_slot": f"{PERIOD_TIMES.get(sp_int, 'Period ' + str(sp_int))} ({dur}h)",
            "status": status_label,
            "note": note
        })

    # Group by Day
    days_order = ["MON", "TUE", "WED", "THU", "FRI"]
    by_day = {d: [] for d in days_order}
    for s in my_sessions:
        if s["day"] in by_day:
            by_day[s["day"]].append(s)

    for d in days_order:
        by_day[d].sort(key=lambda x: x["start_period"])

    total_contact_hours = sum(s["duration"] for s in my_sessions if s["status"] != "CANCEL")
    return {
        "faculty_id": fid,
        "faculty_name": current_user.get("name", "Dr. A. Sharma"),
        "total_lectures": len(my_sessions),
        "total_contact_hours": total_contact_hours,
        "schedule_by_day": by_day,
        "days": [d for d in days_order if by_day[d]],
        "sessions": my_sessions
    }

@router.get("/{faculty_id_or_username}/schedule")
def get_faculty_schedule_by_param(faculty_id_or_username: str):
    users_col = db_manager.get_collection("users")
    u = users_col.find_one({"$or": [
        {"faculty_id": faculty_id_or_username},
        {"username": faculty_id_or_username},
        {"email": faculty_id_or_username}
    ]})
    fid = u.get("faculty_id") if u else faculty_id_or_username
    fname = u.get("name") if u else faculty_id_or_username

    ds = load_default_dataset()
    schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
    assignments = []
    if os.path.exists(schedule_path):
        with open(schedule_path, "r", encoding="utf-8") as f:
            assignments = json.load(f).get("timetable", [])

    my_sessions = []
    for a in assignments:
        s = ds.sessions_by_id.get(a["session_id"])
        if not s or fid not in s.faculty_ids:
            continue

        c = ds.courses_by_code.get(s.course_code)
        cname = c.name if c else s.course_code
        sp_int = int(str(a["start_period"]).replace("P", ""))
        dur = s.duration_hours

        my_sessions.append({
            "session_id": a["session_id"],
            "course_code": s.course_code,
            "course_name": cname,
            "session_type": s.session_type.upper(),
            "group_id": s.student_groups[0] if s.student_groups else "Y1-A",
            "student_groups": s.student_groups,
            "room_id": a["room_id"],
            "day": a["day"].upper()[:3],
            "start_period": sp_int,
            "duration": dur,
            "time_slot": f"{PERIOD_TIMES.get(sp_int, 'Period ' + str(sp_int))} ({dur}h)",
            "status": "ACTIVE"
        })

    days_order = ["MON", "TUE", "WED", "THU", "FRI"]
    by_day = {d: [] for d in days_order}
    for s in my_sessions:
        if s["day"] in by_day:
            by_day[s["day"]].append(s)

    for d in days_order:
        by_day[d].sort(key=lambda x: x["start_period"])

    total_contact_hours = sum(s["duration"] for s in my_sessions)
    return {
        "faculty_id": fid,
        "faculty_name": fname,
        "total_lectures": len(my_sessions),
        "total_contact_hours": total_contact_hours,
        "schedule_by_day": by_day,
        "days": [d for d in days_order if by_day[d]],
        "sessions": my_sessions
    }

@router.get("/vacant-slots")
def get_vacant_slots_for_batch(
    group_id: str = Query(..., description="Target student batch, e.g. Y2-CSE"),
    session_type: str = Query("LECTURE", description="LECTURE | LAB | TUTORIAL"),
    duration: int = Query(1, ge=1, le=3),
    day: Optional[str] = Query(None, description="Optional day filter: MON, TUE, WED, THU, FRI, SAT, SUN"),
    current_user: dict = Depends(get_current_user)
):
    fid = current_user.get("faculty_id") or "F01"
    ds = load_default_dataset()

    # Load baseline schedule
    schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
    assignments = []
    if os.path.exists(schedule_path):
        with open(schedule_path, "r", encoding="utf-8") as f:
            assignments = json.load(f).get("timetable", [])

    # Check which candidate days to evaluate
    if day:
        day_clean = day.upper()[:3]
        if day_clean in ("SAT", "SUN"):
            candidate_days = [day_clean]
        else:
            candidate_days = [d for d in ["MON", "TUE", "WED", "THU", "FRI"] if d == day_clean]
    else:
        candidate_days = ["MON", "TUE", "WED", "THU", "FRI"]

    # Weekday teaching periods: P1..P4 (morning), P6..P9 (afternoon). P5 is lunch!
    teaching_periods = [1, 2, 3, 4, 6, 7, 8, 9]
    vacant_slots = []

    for d in candidate_days:
        for p in teaching_periods:
            block_periods = [p + i for i in range(duration)]
            if any(bp not in teaching_periods for bp in block_periods):
                continue

            # 1. Is student batch free?
            batch_busy = False
            for a in assignments:
                a_day = a["day"].upper()[:3]
                if a_day != d:
                    continue
                s = ds.sessions_by_id.get(a["session_id"])
                if not s or group_id not in s.student_groups:
                    continue
                a_sp = int(str(a["start_period"]).replace("P", ""))
                a_block = [a_sp + j for j in range(s.duration_hours)]
                if any(bp in a_block for bp in block_periods):
                    batch_busy = True
                    break

            if batch_busy:
                continue

            # 2. Is current faculty free?
            faculty_busy = False
            for a in assignments:
                a_day = a["day"].upper()[:3]
                if a_day != d:
                    continue
                s = ds.sessions_by_id.get(a["session_id"])
                if not s or fid not in s.faculty_ids:
                    continue
                a_sp = int(str(a["start_period"]).replace("P", ""))
                a_block = [a_sp + j for j in range(s.duration_hours)]
                if any(bp in a_block for bp in block_periods):
                    faculty_busy = True
                    break

            if faculty_busy:
                continue

            # 3. Find vacant compatible rooms
            occupied_rooms = set()
            for a in assignments:
                a_day = a["day"].upper()[:3]
                if a_day != d:
                    continue
                s = ds.sessions_by_id.get(a["session_id"])
                s_dur = s.duration_hours if s else 1
                a_sp = int(str(a["start_period"]).replace("P", ""))
                a_block = [a_sp + j for j in range(s_dur)]
                if any(bp in a_block for bp in block_periods):
                    occupied_rooms.add(a["room_id"])

            is_lab = session_type.upper() == "LAB"
            free_rooms = []
            for r in ds.rooms:
                if r.id in occupied_rooms:
                    continue
                rtype = r.type.lower()
                if is_lab and ("lab" in rtype):
                    free_rooms.append(r)
                elif not is_lab and ("lecture" in rtype or "classroom" in rtype or "hall" in rtype):
                    free_rooms.append(r)

            if not free_rooms and ds.rooms:
                free_rooms = [r for r in ds.rooms if r.id not in occupied_rooms and r.capacity >= 40]

            if free_rooms:
                end_p = p + duration - 1
                start_label = PERIOD_TIMES.get(p, f"P{p}").split(" - ")[0]
                end_label = PERIOD_TIMES.get(end_p, f"P{end_p}").split(" - ")[-1]
                time_str = f"{start_label} - {end_label}"
                vacant_slots.append({
                    "day": d,
                    "start_period": p,
                    "end_period": end_p,
                    "period_label": f"P{p}" if duration == 1 else f"P{p}-P{end_p}",
                    "time_slot": time_str,
                    "duration": duration,
                    "group_id": group_id,
                    "recommended_room": free_rooms[0].id,
                    "available_rooms": [r.id for r in free_rooms[:6]],
                    "available_rooms_count": len(free_rooms),
                    "room_type": free_rooms[0].type
                })

    return {
        "group_id": group_id,
        "faculty_id": fid,
        "session_type": session_type,
        "duration": duration,
        "vacant_slots_count": len(vacant_slots),
        "vacant_slots": vacant_slots
    }

class LectureActionPayload(BaseModel):
    session_id: str
    action_type: Optional[str] = None
    action: Optional[str] = None
    reason: str = Field(min_length=3, description="Clear academic or medical rationale")
    target_day: Optional[str] = None
    target_period: Optional[int] = None
    target_room: Optional[str] = None

@router.post("/lecture-action")
def modify_lecture(payload: LectureActionPayload, current_user: dict = Depends(get_current_user)):
    fid = current_user.get("faculty_id") or "F01"
    act_str = (payload.action_type or payload.action or "CANCEL").upper()
    action_entry = {
        "action_id": f"ACT_{len(_faculty_actions_store)+1:03d}",
        "faculty_id": fid,
        "faculty_name": current_user.get("name"),
        "session_id": payload.session_id,
        "action_type": act_str,
        "reason": payload.reason,
        "target_day": payload.target_day.upper()[:3] if payload.target_day else None,
        "target_period": payload.target_period,
        "target_room": payload.target_room,
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _faculty_actions_store.append(action_entry)

    # Log in system audit trail
    audit_col = db_manager.get_collection("audit_logs")
    audit_col.insert_one({
        "actor_id": current_user.get("id"),
        "actor_email": current_user.get("email"),
        "action": f"faculty_lecture_{act_str.lower()}_submitted",
        "entity": "session",
        "entity_id": payload.session_id,
        "details": action_entry,
        "ts": datetime.now(timezone.utc).isoformat()
    })

    return {
        "success": True,
        "message": f"Lecture {payload.session_id} {act_str} request submitted to Academic Administrator. Awaiting approval.",
        "action": action_entry
    }

class WeekendRequestPayload(BaseModel):
    course_code: Optional[str] = None
    subject_code: Optional[str] = None
    group_id: Optional[str] = "Y2-CSE"
    day: str = Field(description="Saturday | Sunday | SAT | SUN")
    period_slot: Optional[str] = None
    start_period: Optional[int] = 2
    duration_hours: Optional[int] = None
    duration: Optional[int] = 1
    room_id: Optional[str] = "LH-1"
    reason: str = Field(min_length=3)

@router.post("/weekend-request")
def request_weekend_extra_lecture(payload: WeekendRequestPayload, current_user: dict = Depends(get_current_user)):
    fid = current_user.get("faculty_id") or "F01"
    ds = load_default_dataset()

    code_target = payload.course_code or payload.subject_code or "CS201"
    dur = payload.duration_hours or payload.duration or 1
    group_target = payload.group_id or "Y2-CSE"
    day_val = "Saturday" if "SAT" in payload.day.upper() else "Sunday"

    # Rule: Check that student lecture duration does NOT exceed weekly planned curriculum
    c = ds.courses_by_code.get(code_target)
    planned_credits = c.credits if c else 3
    max_weekly_allowed = planned_credits + 1 # At most 1 makeup hour buffer

    # Calculate current weekly contact hours for this course & group
    current_hours = 0
    for s in ds.sessions:
        if s.course_code == code_target and group_target in s.student_groups:
            current_hours += s.duration_hours

    if current_hours + dur > max_weekly_allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Curriculum Constraint Violation: Total weekly hours for {code_target} ({current_hours}h current + {dur}h requested) would exceed the maximum permitted syllabus limit of {max_weekly_allowed} hours/week for group {group_target}."
        )

    req_entry = {
        "request_id": f"WKD_{len(_weekend_requests_store)+1:03d}",
        "faculty_id": fid,
        "faculty_name": current_user.get("name"),
        "course_code": code_target,
        "course_name": c.name if c else code_target,
        "group_id": group_target,
        "day": day_val,
        "period_slot": payload.period_slot or f"Period {payload.start_period}",
        "duration_hours": dur,
        "room_id": payload.room_id or "LH-1",
        "reason": payload.reason,
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _weekend_requests_store.append(req_entry)

    # Log in system audit trail
    audit_col = db_manager.get_collection("audit_logs")
    audit_col.insert_one({
        "actor_id": current_user.get("id"),
        "actor_email": current_user.get("email"),
        "action": "faculty_weekend_lecture_request_submitted",
        "entity": "weekend_slot",
        "details": req_entry,
        "ts": datetime.now(timezone.utc).isoformat()
    })

    return {
        "success": True,
        "message": f"Weekend extra lecture request for {day_val} submitted to Dean / Administrator for review. Weekly curriculum guard verified.",
        "request": req_entry
    }

@router.get("/requests")
def list_faculty_requests(current_user: dict = Depends(get_current_user)):
    fid = current_user.get("faculty_id") or "F01"
    my_actions = [a for a in _faculty_actions_store if a.get("faculty_id") == fid]
    my_weekend = [w for w in _weekend_requests_store if w.get("faculty_id") == fid]
    all_my_requests = my_actions + my_weekend
    return {
        "requests": all_my_requests,
        "lecture_modifications": my_actions,
        "weekend_requests": my_weekend,
        "total_requests": len(all_my_requests)
    }
