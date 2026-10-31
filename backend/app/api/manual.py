import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.security import require_role, get_current_user
from app.db import db_manager
from app.schemas import ManualAssignmentRequest
from app.scheduler.dataset_adapter import load_default_dataset
from app.validators.hard import validate_hard_constraints

logger = logging.getLogger("cit_scheduler.manual_api")
router = APIRouter(prefix="/manual-assignments", tags=["Manual Scheduling"])

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

    if not t:
        raise HTTPException(status_code=400, detail="No timetable available.")

    assignments = [dict(a) for a in t.get("assignments", [])]
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

    if not t:
        raise HTTPException(status_code=400, detail="No timetable available.")

    assignments = [dict(a) for a in t.get("assignments", [])]
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
