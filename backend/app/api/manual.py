import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.security import require_role, get_current_user
from app.db import db_manager
from app.schemas import ManualAssignmentRequest
from app.scheduler.dataset_adapter import load_default_dataset
from app.validators.hard import validate_hard_constraints

logger = logging.getLogger("cit_scheduler.manual_api")
router = APIRouter(tags=["Manual Scheduling"])

@router.post("/validate")
def validate_manual_assignment(payload: ManualAssignmentRequest):
    """
    Dry run validating a manual assignment against all hard constraints.
    """
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")

    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None
    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else timetables_col.find_one({})

    assignments = [dict(a) for a in t.get("assignments", [])] if t else []
    if not assignments:
        import os, json
        schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
        if os.path.exists(schedule_path):
            try:
                with open(schedule_path, "r", encoding="utf-8") as f:
                    assignments = [dict(a) for a in json.load(f).get("timetable", [])]
            except Exception:
                pass

    if not assignments:
        raise HTTPException(status_code=400, detail="No timetable available.")
    # Replace assignment for the targeted session
    updated = False
    for a in assignments:
        if a["session_id"] == payload.session_id:
            a["day"] = payload.day
            a["start_period"] = payload.start_period
            a["room_id"] = payload.room_id
            updated = True
            break
    if not updated:
        assignments.append({
            "session_id": payload.session_id,
            "day": payload.day,
            "start_period": payload.start_period,
            "room_id": payload.room_id
        })

    ds = load_default_dataset()
    val_res = validate_hard_constraints(ds, assignments)

    return {
        "is_valid": val_res["is_valid"],
        "violations_count": val_res["violations_count"],
        "violations": val_res["violations"],
        "proposed": payload.dict()
    }

@router.post("")
def commit_manual_assignment(
    payload: ManualAssignmentRequest,
    current_user: dict = Depends(require_role(["admin", "coordinator"]))
):
    """
    Applies and commits manual session placement if all constraints pass.
    """
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")
    audit_col = db_manager.get_collection("audit_logs")

    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None
    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else timetables_col.find_one({})

    assignments = [dict(a) for a in t.get("assignments", [])] if t else []
    if not assignments:
        import os, json
        schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
        if os.path.exists(schedule_path):
            try:
                with open(schedule_path, "r", encoding="utf-8") as f:
                    assignments = [dict(a) for a in json.load(f).get("timetable", [])]
            except Exception:
                pass

    if not assignments:
        raise HTTPException(status_code=400, detail="No timetable available.")
    for a in assignments:
        if a["session_id"] == payload.session_id:
            a["day"] = payload.day
            a["start_period"] = payload.start_period
            a["room_id"] = payload.room_id
            break

    ds = load_default_dataset()
    val_res = validate_hard_constraints(ds, assignments)

    if not val_res["is_valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Manual assignment cannot be committed due to hard constraint violations.",
                "violations": val_res["violations"]
            }
        )

    # Increment version
    last_t = timetables_col.find().sort("version", -1).limit(1).to_list()
    new_version = (last_t[0]["version"] + 1) if last_t else 1

    new_t_doc = {
        "version": new_version,
        "status": "published",
        "dataset_version": t.get("dataset_version", "1.0.0"),
        "assignments": assignments,
        "base_version": t.get("version"),
        "created_by": current_user["email"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    timetables_col.insert_one(new_t_doc)
    state_col.update_one({"_id": "state"}, {"$set": {"published_version": new_version}})

    audit_col.insert_one({
        "actor_id": current_user["id"],
        "actor_email": current_user["email"],
        "action": "manual_session_assignment",
        "entity": "session",
        "entity_id": payload.session_id,
        "details": payload.dict(),
        "ts": datetime.now(timezone.utc).isoformat()
    })

    return {
        "message": f"Manual assignment applied. New timetable version {new_version} published.",
        "version": new_version
    }

from typing import Union, Any
from pydantic import BaseModel
class MovePayload(BaseModel):
    session_id: str
    new_day: str
    new_start_period: Union[int, str]
    new_room_id: str

@router.post("/validate-move")
def validate_move(payload: MovePayload):
    ds = load_default_dataset()
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")

    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None
    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else timetables_col.find_one({})

    assignments = [dict(a) for a in t.get("assignments", [])] if t else []
    if not assignments:
        import os, json
        schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
        if os.path.exists(schedule_path):
            with open(schedule_path, "r", encoding="utf-8") as f:
                assignments = [dict(a) for a in json.load(f).get("timetable", [])]

    day_norm = payload.new_day.capitalize()[:3]
    sp_str = str(payload.new_start_period).strip().upper()
    sp_norm = sp_str if sp_str.startswith("P") else f"P{sp_str}"

    for a in assignments:
        if a["session_id"] == payload.session_id:
            a["day"] = day_norm
            a["start_period"] = sp_norm
            a["room_id"] = payload.new_room_id
            break

    val_res = validate_hard_constraints(ds, assignments)
    return {
        "is_valid": val_res["is_valid"],
        "hard_violations": val_res.get("violations", []),
        "soft_penalty_delta": 0 if val_res["is_valid"] else 50
    }

@router.post("/commit-move")
def commit_move(payload: MovePayload, current_user: dict = Depends(get_current_user)):
    ds = load_default_dataset()
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")

    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None
    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else timetables_col.find_one({})

    assignments = [dict(a) for a in t.get("assignments", [])] if t else []
    if not assignments:
        import os, json
        schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
        if os.path.exists(schedule_path):
            with open(schedule_path, "r", encoding="utf-8") as f:
                assignments = [dict(a) for a in json.load(f).get("timetable", [])]

    day_norm = payload.new_day.capitalize()[:3]
    sp_str = str(payload.new_start_period).strip().upper()
    sp_norm = sp_str if sp_str.startswith("P") else f"P{sp_str}"

    for a in assignments:
        if a["session_id"] == payload.session_id:
            a["day"] = day_norm
            a["start_period"] = sp_norm
            a["room_id"] = payload.new_room_id
            break

    s = ds.sessions_by_id.get(payload.session_id)
    c = ds.courses_by_code.get(s.course_code) if s else None

    # Coordinator department restriction and Admin permission flow
    is_coordinator = current_user.get("role") == "coordinator"
    if is_coordinator:
        coord_dept = (current_user.get("department") or "CSE").upper()
        course_dept = (c.department if c else "CSE").upper()
        if course_dept != coord_dept and coord_dept not in course_dept and course_dept not in coord_dept:
            raise HTTPException(
                status_code=403,
                detail=f"Department Scope Violation: As {coord_dept} Coordinator, you can only manage sessions for your own department. Course {s.course_code if s else ''} belongs to {course_dept}."
            )

        from app.api.admin import _coordinator_requests_store
        req_id = f"COORD_{len(_coordinator_requests_store)+1:03d}"
        coord_entry = {
            "request_id": req_id,
            "id": req_id,
            "request_type": "coordinator_request",
            "coordinator_id": current_user.get("id"),
            "coordinator_name": current_user.get("name", "Department Coordinator"),
            "department": coord_dept,
            "session_id": payload.session_id,
            "course_code": s.course_code if s else "Course",
            "course_name": c.name if c else "Course",
            "target_day": payload.new_day.upper()[:3],
            "target_period": int(sp_norm.replace("P", "")),
            "target_room": payload.new_room_id,
            "status": "PENDING_ADMIN_APPROVAL",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        _coordinator_requests_store.append(coord_entry)

        audit_col = db_manager.get_collection("audit_logs")
        audit_col.insert_one({
            "actor_id": current_user.get("id"),
            "actor_email": current_user.get("email"),
            "action": "coordinator_session_relocation_requested",
            "entity": "session",
            "entity_id": payload.session_id,
            "details": coord_entry,
            "ts": datetime.now(timezone.utc).isoformat()
        })

        return {
            "success": True,
            "requires_admin_approval": True,
            "status": "PENDING_ADMIN_APPROVAL",
            "message": f"Session relocation for {payload.session_id} ({s.course_code if s else ''}) submitted to Dean & Administrator for approval. Changes will take effect once approved.",
            "request": coord_entry
        }

    # Save to timetable (Direct Admin action)
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

    sp_int = int(sp_norm.replace("P", ""))
    return {
        "success": True,
        "session": {
            "session_id": payload.session_id,
            "course_code": s.course_code if s else "CS",
            "course_name": c.name if c else "Course",
            "type": s.session_type.upper() if s else "LECTURE",
            "group_id": s.student_groups[0] if (s and s.student_groups) else "Y1-A",
            "faculty_id": s.faculty_ids[0] if (s and s.faculty_ids) else "F01",
            "room_id": payload.new_room_id,
            "day": payload.new_day.upper()[:3],
            "start_period": sp_int,
            "duration": s.duration_hours if s else 1
        }
    }

