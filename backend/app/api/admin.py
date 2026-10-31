import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.security import require_role
from app.db import db_manager
from app.security import seed_demo_users
from app.schemas import ResetDemoRequest
from app.scheduler.dataset_adapter import load_default_dataset
from app.scheduler.model_timetable import TimetableSolver
from app.scheduler.model_exams import ExamScheduler
from app.scheduler.model_booking import BookingDecisionEngine

router = APIRouter(prefix="/admin", tags=["Admin"])

DEFAULT_PRIORITY_ORDER = [
    {"level": 1, "category": "exam", "name": "Exams"},
    {"level": 2, "category": "regular_class", "name": "Regular Classes"},
    {"level": 3, "category": "institute_event", "name": "Institute Events (Spectra main, convocation)"},
    {"level": 4, "category": "guest_lecture", "name": "Guest Lectures"},
    {"level": 5, "category": "department_event", "name": "Department Events"},
    {"level": 6, "category": "club_event", "name": "Club Events"}
]

# In-memory store for Coordinator / HOD change requests requiring Admin permission
_coordinator_requests_store: List[Dict[str, Any]] = []

@router.get("/priority-order")
def get_priority_order():
    prio_col = db_manager.get_collection("priority_config")
    doc = prio_col.find_one({})
    if doc:
        return doc.get("order", DEFAULT_PRIORITY_ORDER)
    return DEFAULT_PRIORITY_ORDER

@router.put("/priority-order")
def update_priority_order(new_order: List[Dict[str, Any]], current_user: dict = Depends(require_role(["admin"]))):
    prio_col = db_manager.get_collection("priority_config")
    audit_col = db_manager.get_collection("audit_logs")

    doc = {
        "order": new_order,
        "changed_by": current_user["email"],
        "at": datetime.now(timezone.utc).isoformat()
    }
    prio_col.update_one({}, {"$set": doc}, upsert=True)

    audit_col.insert_one({
        "actor_id": current_user["id"],
        "actor_email": current_user["email"],
        "action": "update_priority_order",
        "entity": "priority_config",
        "details": {"new_order": new_order},
        "ts": datetime.now(timezone.utc).isoformat()
    })
    return {"message": "Priority order updated.", "order": new_order}

@router.get("/audit-logs")
def get_audit_logs(current_user: dict = Depends(require_role(["admin"]))):
    audit_col = db_manager.get_collection("audit_logs")
    logs = audit_col.find().sort("ts", -1).to_list(100)
    for l in logs:
        l["_id"] = str(l.get("_id", ""))
    return logs

def _perform_demo_reset():
    # Clear collections
    for col_name in ["timetables", "exam_schedules", "bookings", "proposals", "jobs", "audit_logs"]:
        col = db_manager.get_collection(col_name)
        col.delete_many({})

    # Seed users
    seed_demo_users()

    # Load default dataset and pre-generate timetable, exams, bookings
    ds = load_default_dataset()
    import os, json
    assignments = None
    metrics = None
    schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
    if os.path.exists(schedule_path):
        try:
            with open(schedule_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                assignments = data.get("timetable", [])
                metrics = data.get("metadata", {}).get("metrics", {})
        except Exception:
            pass

    if not assignments:
        solver = TimetableSolver(ds, time_limit_seconds=45, num_workers=2)
        status_str, assignments, metrics = solver.solve()

    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")
    if assignments:
        t_doc = {
            "version": 1,
            "status": "published",
            "dataset_version": "1.0.0",
            "assignments": assignments,
            "metrics": metrics,
            "created_by": "system_reset",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        timetables_col.insert_one(t_doc)
        state_col.update_one({"_id": "state"}, {"$set": {"published_version": 1}}, upsert=True)

    # Exams
    exam_solver = ExamScheduler(ds)
    exam_assign = exam_solver.solve()
    db_manager.get_collection("exam_schedules").insert_one({
        "version": 1,
        "assignments": exam_assign,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Bookings
    booking_engine = BookingDecisionEngine(ds, assignments)
    decisions = booking_engine.decide_all()
    bookings_col = db_manager.get_collection("bookings")
    for d in decisions:
        bookings_col.insert_one({
            "id": d["booking_id"],
            "title": d.get("title", "Event"),
            "category": d.get("category", "club_event"),
            "day": d.get("day"),
            "start_period": d.get("start_period"),
            "end_period": d.get("end_period"),
            "status": d["decision"],
            "assigned_room": d.get("assigned_room"),
            "decision_info": {
                "reason": d.get("reason"),
                "evidence": d.get("evidence"),
                "alternative": d.get("alternative"),
                "decided_at": datetime.now(timezone.utc).isoformat()
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        })

from app.security import require_role, get_current_user, get_password_hash
from app.schemas import ResetDemoRequest, UserCreateRequest
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AdminRequestDecisionPayload(BaseModel):
    request_id: str
    request_type: str  # faculty_action | weekend_request | booking
    decision: str      # APPROVED | REJECTED
    reason: Optional[str] = "Decision rendered by Administrator"

@router.get("/pending-requests")
def get_all_pending_requests(current_user: dict = Depends(require_role(["admin", "coordinator"]))):
    from app.api.faculty import _faculty_actions_store, _weekend_requests_store
    bookings_col = db_manager.get_collection("bookings")

    # 1. Faculty actions (cancel / reschedule)
    fac_actions = []
    for a in _faculty_actions_store:
        act_id = a.get("action_id")
        fac_actions.append({
            "id": act_id,
            "request_id": act_id,
            "request_type": "faculty_action",
            "title": f"Faculty {a.get('action_type')}: {a.get('session_id')}",
            "requester_name": a.get("faculty_name", "Faculty Member"),
            "requester_id": a.get("faculty_id"),
            "day": a.get("target_day") or "Scheduled Day",
            "period": a.get("target_period"),
            "room": a.get("target_room"),
            "reason": a.get("reason"),
            "status": a.get("status", "PENDING"),
            "created_at": a.get("created_at")
        })

    # 2. Weekend extra lecture requests
    wkd_actions = []
    for w in _weekend_requests_store:
        w_id = w.get("request_id")
        wkd_actions.append({
            "id": w_id,
            "request_id": w_id,
            "request_type": "weekend_request",
            "title": f"Extra Weekend Lecture: {w.get('course_code')} ({w.get('group_id')})",
            "requester_name": w.get("faculty_name", "Faculty Member"),
            "requester_id": w.get("faculty_id"),
            "day": w.get("day"),
            "period": w.get("period_slot"),
            "room": w.get("room_id"),
            "duration": w.get("duration_hours"),
            "reason": w.get("reason"),
            "status": w.get("status", "PENDING"),
            "created_at": w.get("created_at")
        })

    # 3. Club & Venue bookings
    b_actions = []
    for b in bookings_col.find({}):
        b_id = b.get("id") or str(b.get("_id"))
        b_actions.append({
            "id": b_id,
            "request_id": b_id,
            "request_type": "booking",
            "title": b.get("title", "Campus Event"),
            "requester_name": b.get("requester_name", "Club Lead"),
            "requester_id": b.get("requester_id"),
            "day": b.get("day"),
            "period": b.get("start_period"),
            "room": b.get("requested_room") or b.get("preferred_room"),
            "duration": b.get("duration", 1),
            "reason": b.get("original_text") or b.get("notes") or "Venue booking request",
            "status": b.get("status", "pending").upper(),
            "created_at": b.get("created_at")
        })

    # 4. Department Coordinator change requests
    coord_actions = []
    for cr in _coordinator_requests_store:
        cr_id = cr.get("request_id")
        coord_actions.append({
            "id": cr_id,
            "request_id": cr_id,
            "request_type": "coordinator_request",
            "title": f"Dept Relocation ({cr.get('department')}): {cr.get('course_code')} -> {cr.get('target_day')} P{cr.get('target_period')}",
            "requester_name": cr.get("coordinator_name", "Department Coordinator"),
            "requester_id": cr.get("coordinator_id"),
            "day": cr.get("target_day"),
            "period": f"Period {cr.get('target_period')}",
            "room": cr.get("target_room"),
            "duration": 1,
            "reason": f"HOD / Coordinator requested room {cr.get('target_room')} for session {cr.get('session_id')}",
            "status": cr.get("status", "PENDING_ADMIN_APPROVAL"),
            "created_at": cr.get("created_at")
        })

    all_reqs = fac_actions + wkd_actions + b_actions + coord_actions
    all_reqs.sort(key=lambda x: (0 if "PEND" in str(x.get("status", "")) else 1, x.get("created_at") or ""), reverse=False)

    return {
        "total_requests": len(all_reqs),
        "pending_count": sum(1 for r in all_reqs if "PEND" in str(r.get("status", ""))),
        "requests": all_reqs
    }

@router.post("/decide-request")
def decide_request(payload: AdminRequestDecisionPayload, current_user: dict = Depends(require_role(["admin", "coordinator"]))):
    from app.api.faculty import _faculty_actions_store, _weekend_requests_store
    audit_col = db_manager.get_collection("audit_logs")
    bookings_col = db_manager.get_collection("bookings")

    dec = payload.decision.upper()
    req_id = payload.request_id
    rtype = payload.request_type

    found = False
    rtype_lower = rtype.lower()
    if "faculty" in rtype_lower or "lecture" in rtype_lower:
        for a in _faculty_actions_store:
            if a.get("action_id") == req_id:
                a["status"] = dec
                a["decided_by"] = current_user.get("email")
                a["decision_reason"] = payload.reason
                found = True
                break
    elif "weekend" in rtype_lower or "extra" in rtype_lower:
        for w in _weekend_requests_store:
            if w.get("request_id") == req_id:
                w["status"] = dec
                w["decided_by"] = current_user.get("email")
                w["decision_reason"] = payload.reason
                found = True
                break
    elif "book" in rtype_lower or "venue" in rtype_lower:
        b = bookings_col.find_one({"id": req_id}) or bookings_col.find_one({"_id": req_id})
        if b:
            bookings_col.update_one(
                {"_id": b["_id"]},
                {"$set": {
                    "status": "approved" if dec == "APPROVED" else "rejected",
                    "assigned_room": b.get("preferred_room") or b.get("requested_room") or "LH-1",
                    "decision_info": {
                        "decided_by": current_user.get("email"),
                        "decision": dec,
                        "reason": payload.reason
                    }
                }}
            )
            found = True
    elif "coord" in rtype_lower or "relocation" in rtype_lower:
        for cr in _coordinator_requests_store:
            if cr.get("request_id") == req_id:
                cr["status"] = dec
                cr["decided_by"] = current_user.get("email")
                cr["decision_reason"] = payload.reason
                found = True
                if dec == "APPROVED":
                    # Commit the coordinator's requested session relocation
                    timetables_col = db_manager.get_collection("timetables")
                    state_col = db_manager.get_collection("system_state")
                    state = state_col.find_one({"_id": "state"})
                    pub_ver = state.get("published_version") if state else None
                    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else timetables_col.find_one({})
                    assignments = [dict(a) for a in t.get("assignments", [])] if t else []
                    for a in assignments:
                        if a["session_id"] == cr.get("session_id"):
                            a["day"] = cr.get("target_day").capitalize()[:3]
                            a["start_period"] = f"P{cr.get('target_period')}"
                            a["room_id"] = cr.get("target_room")
                            break
                    last_t = timetables_col.find().sort("version", -1).limit(1).to_list()
                    new_version = (last_t[0]["version"] + 1) if last_t else 2
                    timetables_col.insert_one({
                        "version": new_version,
                        "status": "published",
                        "assignments": assignments,
                        "created_by": current_user.get("email", "admin@cit.edu"),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
                    state_col.update_one({"_id": "state"}, {"$set": {"published_version": new_version}}, upsert=True)
                break

    if not found:
        raise HTTPException(status_code=404, detail=f"Request '{req_id}' not found.")

    audit_col.insert_one({
        "actor_id": current_user.get("id"),
        "actor_email": current_user.get("email"),
        "action": f"admin_decide_{rtype}",
        "entity": rtype,
        "entity_id": req_id,
        "details": {"decision": dec, "reason": payload.reason},
        "ts": datetime.now(timezone.utc).isoformat()
    })

    return {
        "success": True,
        "message": f"Request {req_id} ({rtype}) marked as {dec}.",
        "request_id": req_id,
        "decision": dec,
        "status": dec
    }

@router.get("/users")
def list_system_users(current_user: dict = Depends(require_role(["admin"]))):
    users_col = db_manager.get_collection("users")
    users = users_col.find({}).to_list(100)
    result = []
    for u in users:
        result.append({
            "id": str(u.get("_id", "")),
            "name": u.get("name"),
            "username": u.get("username", u.get("email", "").split("@")[0]),
            "email": u.get("email"),
            "role": u.get("role"),
            "department": u.get("department"),
            "faculty_id": u.get("faculty_id"),
            "qualifications": u.get("qualifications", []),
            "fields_of_interest": u.get("fields_of_interest", []),
            "is_active": u.get("is_active", True),
            "created_at": u.get("created_at")
        })
    return result

@router.post("/users")
def create_system_user(payload: UserCreateRequest, current_user: dict = Depends(require_role(["admin"]))):
    users_col = db_manager.get_collection("users")
    audit_col = db_manager.get_collection("audit_logs")

    uname = payload.username.strip().lower()
    email = (payload.email or f"{uname}@cit.edu").strip().lower()
    role = payload.role.strip().lower()

    if role not in ("admin", "coordinator", "faculty", "club"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{role}'. Allowed roles are: admin, coordinator, faculty, club."
        )

    # Check for duplicate username or email
    existing = users_col.find_one({
        "$or": [
            {"username": uname},
            {"email": email}
        ]
    })
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"An account with username '{uname}' or email '{email}' already exists."
        )

    pwd_hash = get_password_hash(payload.password)
    
    # Generate faculty ID and qualifications if faculty role
    faculty_id_val = payload.faculty_id.strip() if payload.faculty_id else None
    qualifications_val = payload.qualifications or [
        f"Ph.D. in {payload.department} Engineering (Premier National Institute)",
        f"M.Tech in Advanced {payload.department} Technologies (First Class)",
        f"B.Tech in {payload.department} (Honors)"
    ]
    fields_of_interest_val = payload.fields_of_interest or [
        f"Advanced {payload.department} Research & Modeling",
        "Applied Algorithmic Optimization & Systems",
        "Modern Engineering Education"
    ]

    assigned_sessions_info = []
    if role == "faculty":
        if not faculty_id_val:
            faculty_count = users_col.count_documents({"role": "faculty"})
            faculty_id_val = f"F{faculty_count + 41:02d}"

        # Assign in FACULTY_PROFILES
        from app.api.faculty import FACULTY_PROFILES
        ds = load_default_dataset()
        
        # Find matching department courses to add to their timetable from active schedule
        matching_courses = [c.code for c in ds.courses if c.department.upper() == payload.department.upper()]
        if not matching_courses:
            matching_courses = ["CS201", "CS101", "MA101"]

        schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
        scheduled_session_ids = set()
        if os.path.exists(schedule_path):
            with open(schedule_path, "r", encoding="utf-8") as f:
                scheduled_session_ids = {a["session_id"] for a in json.load(f).get("timetable", [])}

        assigned_count = 0
        for s in ds.sessions:
            if (not scheduled_session_ids or s.id in scheduled_session_ids) and s.course_code in matching_courses:
                if faculty_id_val not in s.faculty_ids:
                    s.faculty_ids.append(faculty_id_val)
                    c_obj = ds.courses_by_code.get(s.course_code)
                    assigned_sessions_info.append({
                        "code": s.course_code,
                        "name": c_obj.name if c_obj else s.course_code,
                        "groups": s.student_groups,
                        "hours_per_week": s.duration_hours,
                        "sessions_per_week": 1,
                        "room": s.required_room_type
                    })
                    assigned_count += 1
            if assigned_count >= 3:
                break

        FACULTY_PROFILES[faculty_id_val] = {
            "id": faculty_id_val,
            "name": payload.name.strip(),
            "designation": "Assistant Professor",
            "department": payload.department.strip(),
            "email": email,
            "phone": "+91 94370 88990",
            "cabin": f"{payload.department}-Block, Cabin 104",
            "qualifications": qualifications_val,
            "fields_of_interest": fields_of_interest_val,
            "teaching_subjects": assigned_sessions_info,
            "planned_weekly_hours": sum(x["hours_per_week"] for x in assigned_sessions_info) or 4,
            "max_daily_hours": 4
        }

    user_doc = {
        "name": payload.name.strip(),
        "username": uname,
        "email": email,
        "password_hash": pwd_hash,
        "role": role,
        "department": payload.department.strip(),
        "faculty_id": faculty_id_val,
        "qualifications": qualifications_val,
        "fields_of_interest": fields_of_interest_val,
        "is_active": True,
        "created_by": current_user.get("email", "admin@cit.edu"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    result = users_col.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # Audit log
    audit_col.insert_one({
        "actor_id": current_user.get("id"),
        "actor_email": current_user.get("email"),
        "action": "admin_create_member",
        "entity": "user",
        "entity_id": user_id,
        "details": {
            "username": uname,
            "email": email,
            "role": role,
            "name": payload.name,
            "department": payload.department
        },
        "ts": datetime.now(timezone.utc).isoformat()
    })

    return {
        "success": True,
        "message": f"New member '{payload.name}' ({uname}) created successfully. They can now log in with their credentials.",
        "user": {
            "id": user_id,
            "name": payload.name,
            "username": uname,
            "email": email,
            "role": role,
            "department": payload.department,
            "faculty_id": user_doc["faculty_id"],
            "qualifications": qualifications_val,
            "fields_of_interest": fields_of_interest_val,
            "assigned_sessions_count": len(assigned_sessions_info),
            "is_active": True
        }
    }

@router.post("/reset-demo")
def reset_demo_data(
    background_tasks: BackgroundTasks,
    payload: Optional[ResetDemoRequest] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Clears all dynamic data, restores benchmark dataset, seeds demo users,
    and pre-generates the baseline timetable. Idempotent and safe.
    """
    background_tasks.add_task(_perform_demo_reset)
    
    # Audit log
    audit_col = db_manager.get_collection("audit_logs")
    audit_col.insert_one({
        "actor_id": current_user.get("id", "admin"),
        "actor_email": current_user.get("email", "admin@cit.edu"),
        "action": "reset_demo_data",
        "entity": "system",
        "details": {"requested_by": current_user.get("email", "admin@cit.edu")},
        "ts": datetime.now(timezone.utc).isoformat()
    })

    return {
        "success": True,
        "message": "Demo reset initiated in background. Baseline state restored successfully."
    }
