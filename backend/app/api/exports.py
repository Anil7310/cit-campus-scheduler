import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from app.db import db_manager
from app.scheduler.dataset_adapter import load_default_dataset

router = APIRouter(prefix="/exports", tags=["Exports"])

@router.get("/schedule.json")
@router.get("/schedule")
def export_schedule():
    # If exports/schedule.json exists on disk, return it, or construct from DB
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    timetables_col = db_manager.get_collection("timetables")
    exams_col = db_manager.get_collection("exam_schedules")
    bookings_col = db_manager.get_collection("bookings")

    t = timetables_col.find_one({"status": "published"}) or timetables_col.find_one({})
    ex = exams_col.find_one({})
    b_list = bookings_col.find({}).to_list(100)

    return {
        "metadata": {
            "dataset_version": "1.0.0",
            "solver_status": "OPTIMAL"
        },
        "timetable": t.get("assignments", []) if t else [],
        "exams": ex.get("assignments", []) if ex else [],
        "bookings": [
            {
                "booking_id": b.get("id"),
                "decision": b.get("status"),
                "assigned_room": b.get("assigned_room"),
                "reason": b.get("decision_info", {}).get("reason", "")
            }
            for b in b_list
        ]
    }

@router.get("/schedule_after.json")
@router.get("/schedule_after")
def export_schedule_after():
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule_after.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    proposals_col = db_manager.get_collection("proposals")
    approved_prop = proposals_col.find_one({"status": "approved"})
    if approved_prop:
        return {
            "metadata": {
                "base_version": approved_prop.get("base_version"),
                "moved_sessions_count": approved_prop.get("moved_count")
            },
            "timetable": approved_prop.get("proposed_schedule", []),
            "diff": approved_prop.get("diff", [])
        }
    raise HTTPException(status_code=404, detail="schedule_after.json not yet generated.")
