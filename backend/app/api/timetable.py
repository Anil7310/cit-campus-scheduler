import logging
import threading
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.security import require_role, get_current_user
from app.db import db_manager
from app.scheduler.dataset_adapter import Dataset, load_default_dataset
from app.scheduler.model_timetable import TimetableSolver
from app.validators.hard import validate_hard_constraints
from app.validators.official import run_official_validator
from app.services.explain import generate_session_explanation
from app.schemas import TimetableGenerateRequest

logger = logging.getLogger("cit_scheduler.timetable_api")
router = APIRouter(prefix="/timetables", tags=["Timetable"])

_solver_lock = threading.Lock()

def _run_solver_background(job_id: str, time_limit: int, auto_publish: bool, user_email: str):
    jobs_col = db_manager.get_collection("jobs")
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")

    jobs_col.update_one({"_id": job_id}, {"$set": {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()}})

    try:
        ds = load_default_dataset()
        solver = TimetableSolver(ds, time_limit_seconds=time_limit, num_workers=2)
        status_str, assignments, metrics = solver.solve()

        if status_str not in ("OPTIMAL", "FEASIBLE") or not assignments:
            jobs_col.update_one({"_id": job_id}, {
                "$set": {
                    "status": "failed",
                    "error": f"Solver status: {status_str}",
                    "finished_at": datetime.now(timezone.utc).isoformat()
                }
            })
            return

        # Validate
        hard_val = validate_hard_constraints(ds, assignments)

        # Version calculation
        last_t = timetables_col.find().sort("version", -1).limit(1).to_list()
        new_version = (last_t[0]["version"] + 1) if last_t else 1

        t_doc = {
            "version": new_version,
            "status": "published" if auto_publish else "draft",
            "dataset_version": ds.metadata.get("version", "1.0.0"),
            "assignments": assignments,
            "metrics": metrics,
            "validation": hard_val,
            "created_by": user_email,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        res = timetables_col.insert_one(t_doc)

        if auto_publish:
            state_col.update_one({"_id": "state"}, {"$set": {"published_version": new_version}}, upsert=True)

        jobs_col.update_one({"_id": job_id}, {
            "$set": {
                "status": "succeeded",
                "result_ref": str(res.inserted_id),
                "version": new_version,
                "metrics": metrics,
                "finished_at": datetime.now(timezone.utc).isoformat()
            }
        })
        logger.info(f"Timetable generation job {job_id} succeeded. Version: {new_version}")

    except Exception as e:
        logger.error(f"Solver job failed with exception: {e}")
        jobs_col.update_one({"_id": job_id}, {
            "$set": {
                "status": "failed",
                "error": str(e),
                "finished_at": datetime.now(timezone.utc).isoformat()
            }
        })

@router.post("/generate")
def generate_timetable(
    payload: TimetableGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["admin"]))
):
    jobs_col = db_manager.get_collection("jobs")
    # Check if a solver job is already running
    active_job = jobs_col.find_one({"status": "running"})
    if active_job:
        raise HTTPException(
            status_code=409,
            detail="A timetable generation job is already in progress. Please wait for it to complete."
        )

    job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    job_doc = {
        "_id": job_id,
        "type": "timetable_generation",
        "status": "queued",
        "progress": 0,
        "params": payload.dict(),
        "created_by": current_user["email"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    jobs_col.insert_one(job_doc)

    time_limit = payload.time_limit_seconds or 60
    background_tasks.add_task(
        _run_solver_background,
        job_id,
        time_limit,
        payload.auto_publish,
        current_user["email"]
    )

    return {"job_id": job_id, "status": "queued", "message": "Timetable generation started in background."}

@router.get("/current")
def get_current_timetable():
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")

    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None

    if pub_ver:
        timetable = timetables_col.find_one({"version": pub_ver})
        if timetable:
            timetable["id"] = str(timetable.get("_id", ""))
            return timetable

    # If no published version, find latest draft or any
    latest = timetables_col.find().sort("version", -1).limit(1).to_list()
    if latest:
        t = latest[0]
        t["id"] = str(t.get("_id", ""))
        return t

    return {"message": "No timetable available yet.", "assignments": []}

@router.get("/versions")
def get_timetable_versions():
    timetables_col = db_manager.get_collection("timetables")
    versions = timetables_col.find().sort("version", -1).to_list(100)
    for v in versions:
        v["id"] = str(v.get("_id", ""))
        v.pop("assignments", None) # Exclude large list for summary
    return versions

@router.post("/{version}/publish")
def publish_timetable(version: int, current_user: dict = Depends(require_role(["admin"]))):
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")

    target = timetables_col.find_one({"version": version})
    if not target:
        raise HTTPException(status_code=404, detail=f"Timetable version {version} not found.")

    timetables_col.update_one({"version": version}, {"$set": {"status": "published"}})
    state_col.update_one({"_id": "state"}, {"$set": {"published_version": version}}, upsert=True)

    return {"message": f"Timetable version {version} published successfully."}

@router.get("/{version}/explain/{session_id}")
def explain_session(version: int, session_id: str):
    timetables_col = db_manager.get_collection("timetables")
    timetable = timetables_col.find_one({"version": version})
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found.")

    ds = load_default_dataset()
    explanation = generate_session_explanation(session_id, timetable.get("assignments", []), ds)
    return explanation
