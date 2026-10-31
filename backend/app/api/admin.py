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

@router.post("/reset-demo")
def reset_demo_data(
    payload: ResetDemoRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["admin"]))
):
    """
    Clears all dynamic data, restores benchmark dataset, seeds demo users,
    and pre-generates the baseline timetable. Idempotent and safe.
    """
    if payload.confirm != "RESET":
        raise HTTPException(
            status_code=400,
            detail="Confirmation text must be exactly 'RESET' to confirm demo data reset."
        )

    background_tasks.add_task(_perform_demo_reset)
    
    # Audit log
    audit_col = db_manager.get_collection("audit_logs")
    audit_col.insert_one({
        "actor_id": current_user["id"],
        "actor_email": current_user["email"],
        "action": "reset_demo_data",
        "entity": "system",
        "details": {"requested_by": current_user["email"]},
        "ts": datetime.now(timezone.utc).isoformat()
    })

    return {"message": "Demo reset initiated in background. Baseline state will be restored within ~30-60 seconds."}
