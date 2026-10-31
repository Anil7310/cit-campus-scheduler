from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.security import require_role
from app.db import db_manager
from app.scheduler.dataset_adapter import load_default_dataset
from app.scheduler.model_exams import ExamScheduler

router = APIRouter(prefix="/exams", tags=["Exams"])

@router.get("")
def get_exam_schedule():
    ds = load_default_dataset()
    exams_col = db_manager.get_collection("exam_schedules")
    latest = exams_col.find().sort("version", -1).limit(1).to_list()
    raw_assignments = []
    if latest:
        raw_assignments = latest[0].get("assignments", [])
    
    if not raw_assignments:
        scheduler = ExamScheduler(ds)
        raw_assignments = scheduler.solve()
        doc = {
            "version": 1,
            "assignments": raw_assignments,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        exams_col.insert_one(doc)

    # Format into frontend Exam objects
    result = []
    for a in raw_assignments:
        eid = a.get("exam_id")
        cc = a.get("course_code")
        c = ds.courses_by_code.get(cc)
        day_str = a.get("day", "Mon").upper()[:3]
        sp = a.get("start_period", "P2")
        slot = "MORNING" if sp in ("P1", "P2", "P3", "P4") else "AFTERNOON"
        rooms = a.get("room_ids") or ([a.get("room_id")] if a.get("room_id") else ["AUD"])
        
        result.append({
            "exam_id": eid,
            "course_code": cc,
            "course_name": c.name if c else cc,
            "student_groups": a.get("student_groups", []),
            "total_students": a.get("total_students", 60),
            "day": day_str,
            "slot": slot,
            "rooms": rooms,
            "effective_capacities": a.get("effective_capacities", {})
        })
    return result

@router.post("/generate")
def generate_exams(current_user: dict = Depends(require_role(["admin"]))):
    ds = load_default_dataset()
    scheduler = ExamScheduler(ds)
    assignments = scheduler.solve()

    exams_col = db_manager.get_collection("exam_schedules")
    last = exams_col.find().sort("version", -1).limit(1).to_list()
    new_ver = (last[0]["version"] + 1) if last else 1

    doc = {
        "version": new_ver,
        "assignments": assignments,
        "created_by": current_user["email"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    res = exams_col.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    return doc
