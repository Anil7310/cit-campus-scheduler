from fastapi import APIRouter, HTTPException
from app.db import db_manager

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/{job_id}")
def get_job_status(job_id: str):
    jobs_col = db_manager.get_collection("jobs")
    job = jobs_col.find_one({"_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return {
        "job_id": job.get("_id"),
        "type": job.get("type"),
        "status": job.get("status"),
        "progress": job.get("progress", 0),
        "result_ref": job.get("result_ref"),
        "version": job.get("version"),
        "metrics": job.get("metrics"),
        "error": job.get("error"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at")
    }

@router.get("")
def list_jobs():
    jobs_col = db_manager.get_collection("jobs")
    jobs = jobs_col.find().sort("created_at", -1).to_list(50)
    for j in jobs:
        j["job_id"] = str(j.get("_id", ""))
    return jobs
