import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.security import require_role, get_current_user
from app.db import db_manager
from app.scheduler.dataset_adapter import Dataset, load_default_dataset

logger = logging.getLogger("cit_scheduler.datasets")
router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.get("/status")
def get_dataset_status():
    ds_col = db_manager.get_collection("datasets")
    active_ds = ds_col.find_one({"is_active": True})
    if active_ds:
        return {
            "is_loaded": True,
            "version": active_ds.get("version", "1.0.0"),
            "uploaded_at": active_ds.get("uploaded_at"),
            "summary": active_ds.get("summary", {})
        }
    else:
        # Load sample summary
        try:
            sample = load_default_dataset()
            summary = {
                "rooms": len(sample.rooms),
                "faculty": len(sample.faculty),
                "student_groups": len(sample.student_groups),
                "courses": len(sample.courses),
                "sessions": len(sample.sessions),
                "exams": len(sample.exams),
                "bookings": len(sample.booking_requests)
            }
            return {
                "is_loaded": True,
                "version": "1.0.0 (Sample)",
                "summary": summary
            }
        except Exception:
            return {"is_loaded": False, "summary": {}}

@router.post("/validate")
async def validate_dataset(file: UploadFile = File(...)):
    """
    Validates uploaded JSON or bundle without saving, returning counts, warnings, and errors.
    """
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON dataset files are supported for validation.")

    try:
        content = await file.read()
        raw_json = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse JSON: {str(e)}")

    errors = []
    warnings = []

    # Schema relationships checks
    rooms = raw_json.get("rooms", [])
    faculty = raw_json.get("faculty", [])
    groups = raw_json.get("student_groups", [])
    courses = raw_json.get("courses", [])
    sessions = raw_json.get("sessions", [])

    room_ids = {r.get("id") for r in rooms}
    fac_ids = {f.get("id") for f in faculty}
    group_ids = {g.get("id") for g in groups}
    course_codes = {c.get("code") for c in courses}

    for idx, s in enumerate(sessions):
        sid = s.get("id", f"index_{idx}")
        # Check course
        cc = s.get("course_code")
        if cc not in course_codes:
            errors.append(f"sessions[{idx}].course_code '{cc}' not found in courses.")
        # Check faculty
        for fid in s.get("faculty_ids", []):
            if fid not in fac_ids:
                errors.append(f"sessions[{idx}].faculty_ids: '{fid}' not found in faculty.")
        # Check groups
        for gid in s.get("student_groups", []):
            if gid not in group_ids:
                errors.append(f"sessions[{idx}].student_groups: '{gid}' not found in student groups.")

    summary = {
        "rooms": len(rooms),
        "faculty": len(faculty),
        "student_groups": len(groups),
        "courses": len(courses),
        "sessions": len(sessions),
        "exams": len(raw_json.get("exams", [])),
        "bookings": len(raw_json.get("booking_requests", []))
    }

    return {
        "is_valid": len(errors) == 0,
        "summary": summary,
        "errors": errors,
        "warnings": warnings
    }

@router.post("/import")
async def import_dataset(file: UploadFile = File(...), current_user: dict = Depends(require_role(["admin"]))):
    """
    Imports and activates a new dataset.
    """
    content = await file.read()
    raw_json = json.loads(content.decode("utf-8"))

    ds_col = db_manager.get_collection("datasets")
    # Deactivate current active datasets
    ds_col.update_one({"is_active": True}, {"$set": {"is_active": False}})

    summary = {
        "rooms": len(raw_json.get("rooms", [])),
        "faculty": len(raw_json.get("faculty", [])),
        "student_groups": len(raw_json.get("student_groups", [])),
        "courses": len(raw_json.get("courses", [])),
        "sessions": len(raw_json.get("sessions", [])),
        "exams": len(raw_json.get("exams", [])),
        "bookings": len(raw_json.get("booking_requests", []))
    }

    doc = {
        "version": raw_json.get("metadata", {}).get("version", f"custom_{datetime.now().strftime('%Y%m%d%H%M')}"),
        "uploaded_by": current_user["email"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "raw": raw_json,
        "summary": summary,
        "is_active": True
    }
    ds_col.insert_one(doc)

    return {"message": "Dataset imported and activated successfully.", "summary": summary}

@router.post("/load-sample")
def load_sample_dataset(current_user: dict = Depends(require_role(["admin"]))):
    """
    Reloads the bundled CIT benchmark sample dataset.
    """
    ds = load_default_dataset()
    ds_col = db_manager.get_collection("datasets")
    ds_col.update_one({"is_active": True}, {"$set": {"is_active": False}})

    summary = {
        "rooms": len(ds.rooms),
        "faculty": len(ds.faculty),
        "student_groups": len(ds.student_groups),
        "courses": len(ds.courses),
        "sessions": len(ds.sessions),
        "exams": len(ds.exams),
        "bookings": len(ds.booking_requests)
    }

    doc = {
        "version": "1.0.0",
        "uploaded_by": "system",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "raw": ds.raw,
        "summary": summary,
        "is_active": True
    }
    ds_col.insert_one(doc)
    return {"message": "Sample CIT dataset loaded successfully.", "summary": summary}

@router.get("/rooms")
def get_rooms():
    ds = load_default_dataset()
    result = []
    for r in ds.rooms:
        rtype = "CLASSROOM"
        t_low = r.type.lower()
        if "lab" in t_low:
            rtype = "LAB"
        elif "auditorium" in t_low or "oat" in t_low or "theatre" in t_low:
            rtype = "AUDITORIUM"
        elif "seminar" in t_low:
            rtype = "SEMINAR_HALL"

        result.append({
            "room_id": r.id,
            "name": r.name,
            "building": "Central Complex" if ("aud" in r.id.lower() or "oat" in r.id.lower()) else "Academic Block",
            "floor": 1 if any(c in r.id for c in ["1", "A"]) else 2,
            "capacity": r.capacity,
            "type": rtype,
            "features": r.features or ["PROJECTOR", "AC", "WHITEBOARD"],
            "is_active": True
        })
    return result

@router.get("/faculty")
def get_faculty():
    ds = load_default_dataset()
    result = []
    for f in ds.faculty:
        result.append({
            "faculty_id": f.id,
            "name": f.name,
            "department": f.department,
            "designation": "Associate Professor" if "Prof." in f.name else "Assistant Professor",
            "email": f"{f.id.lower()}@cit.edu",
            "max_hours_per_day": f.daily_limit_hours
        })
    return result

@router.get("/groups")
def get_groups():
    ds = load_default_dataset()
    result = []
    for g in ds.student_groups:
        dept = "CSE" if "cse" in g.name.lower() or "cs" in g.id.lower() else ("ECE" if "ece" in g.name.lower() or "ec" in g.id.lower() else "Engineering")
        result.append({
            "group_id": g.id,
            "name": g.name,
            "department": dept,
            "year": g.year,
            "section": g.name.split("-")[-1] if "-" in g.name else "A",
            "strength": g.size
        })
    return result

@router.get("/courses")
def get_courses():
    ds = load_default_dataset()
    course_sessions = {}
    for s in ds.sessions:
        if s.course_code not in course_sessions:
            course_sessions[s.course_code] = []
        course_sessions[s.course_code].append(s)

    result = []
    for c in ds.courses:
        sessions = course_sessions.get(c.code, [])
        session_types = list(set(s.session_type.upper() for s in sessions)) if sessions else ["LECTURE"]
        weekly_hours = sum(s.duration_hours for s in sessions)
        faculty_set = set()
        for s in sessions:
            for fid in s.faculty_ids:
                f_obj = ds.faculty_by_id.get(fid)
                if f_obj:
                    faculty_set.add(f"{f_obj.name} ({fid})")
                else:
                    faculty_set.add(fid)

        result.append({
            "code": c.code,
            "name": c.name,
            "department": c.department,
            "year": c.year,
            "credits": c.credits,
            "session_types": session_types,
            "weekly_hours": weekly_hours if weekly_hours > 0 else (c.credits or 3),
            "sessions_count": len(sessions),
            "instructors": sorted(list(faculty_set)),
            "level": f"Year {c.year} Undergraduate"
        })
    return result


