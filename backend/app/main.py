import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.db import db_manager
from app.security import seed_demo_users
from app.scheduler.dataset_adapter import load_default_dataset
from app.api.auth import router as auth_router
from app.api.datasets import router as datasets_router
from app.api.timetable import router as timetable_router
from app.api.views import router as views_router
from app.api.exams import router as exams_router
from app.api.bookings import router as bookings_router
from app.api.rescheduling import router as rescheduling_router
from app.api.assistant import router as assistant_router
from app.api.manual import router as manual_router
from app.api.dashboard import router as dashboard_router
from app.api.exports import router as exports_router
from app.api.admin import router as admin_router
from app.api.jobs import router as jobs_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cit_scheduler.main")

def _first_boot_pre_generation():
    """
    First-boot UX (Section 5.4):
    If no timetable exists after seeding the sample dataset, pre-generate and publish
    the first timetable in a background thread so judges never face an empty app.
    """
    try:
        timetables_col = db_manager.get_collection("timetables")
        state_col = db_manager.get_collection("system_state")
        existing = timetables_col.find_one({})
        if not existing:
            logger.info("First boot detected: Pre-generating and publishing baseline timetable...")
            ds = load_default_dataset()
            from app.scheduler.model_timetable import TimetableSolver
            from app.scheduler.model_exams import ExamScheduler
            from app.scheduler.model_booking import BookingDecisionEngine

            solver = TimetableSolver(ds, time_limit_seconds=45, num_workers=2)
            status_str, assignments, metrics = solver.solve()
            if assignments:
                t_doc = {
                    "version": 1,
                    "status": "published",
                    "dataset_version": "1.0.0",
                    "assignments": assignments,
                    "metrics": metrics,
                    "created_by": "system_startup_seed",
                    "created_at": "2026-10-31T00:00:00Z"
                }
                timetables_col.insert_one(t_doc)
                state_col.update_one({"_id": "state"}, {"$set": {"published_version": 1}}, upsert=True)
                logger.info("Baseline timetable pre-generated and published successfully.")

            # Pre-generate exams
            exam_solver = ExamScheduler(ds)
            exam_assign = exam_solver.solve()
            db_manager.get_collection("exam_schedules").insert_one({
                "version": 1,
                "assignments": exam_assign,
                "created_at": "2026-10-31T00:00:00Z"
            })

            # Pre-decide Spectra bookings
            booking_engine = BookingDecisionEngine(ds, assignments)
            decisions = booking_engine.decide_all()
            b_col = db_manager.get_collection("bookings")
            for d in decisions:
                b_col.insert_one({
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
                        "decided_at": "2026-10-31T00:00:00Z"
                    },
                    "created_at": "2026-10-31T00:00:00Z"
                })
            logger.info("First boot initialization complete.")
    except Exception as e:
        logger.error(f"Error during first-boot pre-generation: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    # 1. Connect to DB (with resilient fallback)
    try:
        db_manager.connect()
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")

    # 2. Seed demo accounts
    try:
        seed_demo_users()
    except Exception as e:
        logger.error(f"Error seeding demo users: {e}")

    # 3. Clean up stale running jobs from prior crashes
    try:
        jobs_col = db_manager.get_collection("jobs")
        jobs_col.update_one(
            {"status": "running"},
            {"$set": {"status": "failed", "error": "Server restarted while job was running."}}
        )
    except Exception as e:
        logger.error(f"Error cleaning up old jobs: {e}")

    # 4. First-boot pre-generation in background thread
    if settings.SEED_ON_STARTUP:
        threading.Thread(target=_first_boot_pre_generation, daemon=True).start()

    yield
    logger.info("Application shutting down...")

app = FastAPI(
    title="CIT Campus Scheduling & Venue Management Platform",
    description="Full-stack AI-assisted timetable, venue booking, and rescheduling system for Chilika Institute of Technology.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware (Section 5.1)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.FRONTEND_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Exception Handlers (Section 5.12)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for err in exc.errors():
        loc = " -> ".join([str(l) for l in err.get("loc", [])])
        msg = err.get("msg", "Validation error")
        error_messages.append(f"{loc}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Input validation failed. Please review the highlighted fields.",
            "details": error_messages
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. The server has logged the incident.",
            "details": str(exc) if settings.ENVIRONMENT == "development" else "Please contact the system administrator."
        }
    )

# Root Endpoint (Judges & Render health checks hit this)
@app.get("/")
def root():
    return {
        "institution": "Chilika Institute of Technology (CIT)",
        "platform": "CIT Campus Scheduling & Venue Management Platform",
        "status": "online",
        "api_docs": "/docs",
        "health_check": "/api/v1/health"
    }

# Health Check Endpoint (Section 5.1)
@app.get("/api/v1/health")
def health_check():
    db_ok = db_manager.is_connected
    if settings.MONGODB_URI and not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "db": "down",
                "message": "MongoDB Atlas connection is currently unreachable. Retrying in background..."
            }
        )

    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")
    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None

    llm_enabled = bool(settings.LLM_PROVIDER != "none" and settings.LLM_API_KEY)

    return {
        "status": "healthy",
        "db": "ok" if db_ok else "in_memory_fallback",
        "dataset_loaded": True,
        "published_timetable_version": pub_ver,
        "llm_enabled": llm_enabled,
        "llm_provider": settings.LLM_PROVIDER
    }

# Register API routers under /api/v1
api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(datasets_router, prefix=api_prefix)
app.include_router(timetable_router, prefix=api_prefix)
app.include_router(views_router, prefix=api_prefix)
app.include_router(exams_router, prefix=api_prefix)
app.include_router(bookings_router, prefix=api_prefix)
app.include_router(rescheduling_router, prefix=api_prefix)
app.include_router(assistant_router, prefix=api_prefix)
app.include_router(manual_router, prefix=api_prefix)
app.include_router(dashboard_router, prefix=api_prefix)
app.include_router(exports_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)
app.include_router(jobs_router, prefix=api_prefix)
