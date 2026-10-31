from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.security import require_role
from app.db import db_manager
from app.scheduler.dataset_adapter import load_default_dataset
from app.scheduler.model_exams import ExamScheduler

router = APIRouter(prefix="/exams", tags=["Exams"])

@router.get("")
def get_exam_schedule():
    exams_col = db_manager.get_collection("exam_schedules")
    latest = exams_col.find().sort("version", -1).limit(1).to_list()
    if latest:
        doc = latest[0]
        doc["id"] = str(doc.get("_id", ""))
        return doc

    # Pre-generate if empty
    ds = load_default_dataset()
    scheduler = ExamScheduler(ds)
    assignments = scheduler.solve()
    doc = {
        "version": 1,
        "assignments": assignments,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    res = exams_col.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    return doc

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
