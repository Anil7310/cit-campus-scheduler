import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from app.security import get_current_user
from app.schemas import AssistantParseRequest, AssistantScheduleRequest
from app.ai.provider import llm_provider
from app.db import db_manager
from app.scheduler.dataset_adapter import load_default_dataset
from app.scheduler.repair import ReschedulingEngine
from app.validators.hard import validate_hard_constraints

logger = logging.getLogger("cit_scheduler.assistant_api")
router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

@router.post("/booking-parse")
async def parse_booking_nl(payload: AssistantParseRequest, current_user: dict = Depends(get_current_user)):
    """
    Parses plain English or Hinglish venue request into a structured draft booking.
    Falls back seamlessly to regex/Hinglish dictionary parser if LLM is unavailable.
    """
    user_role = current_user.get("role", "club")
    parsed_draft = await llm_provider.parse_booking_request(payload.message, user_role=user_role)
    return {
        "success": True,
        "draft": parsed_draft,
        "llm_used": parsed_draft.get("llm_used", False),
        "parser": parsed_draft.get("parser", "fallback")
    }

@router.post("/schedule-request")
async def handle_schedule_request_nl(payload: AssistantScheduleRequest, current_user: dict = Depends(get_current_user)):
    """
    Faculty natural language leave / reschedule request.
    Verifies user faculty ownership, runs repair solver, and returns validated proposal.
    """
    faculty_id = current_user.get("faculty_id")
    if not faculty_id and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="You must be linked to an instructor ID to submit faculty schedule change requests."
        )

    # Use F01 default if admin testing
    fid = faculty_id or "F01"
    parsed_intent = await llm_provider.parse_schedule_request(payload.message, fid, current_user.get("role", "faculty"))

    # Convert to disruption
    disruption = {
        "id": f"DISRUPT_FAC_{fid}_{datetime.now().strftime('%m%d%H%M')}",
        "type": "faculty_leave",
        "faculty_id": fid,
        "day": parsed_intent.get("day", "Tue"),
        "start_period": parsed_intent.get("start_period", "P1"),
        "end_period": parsed_intent.get("end_period", "P4"),
        "reason": parsed_intent.get("reason", payload.message)
    }

    # Run repair engine to see if a valid solution exists
    ds = load_default_dataset()
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")

    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None
    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else timetables_col.find_one({})

    if not t:
        raise HTTPException(status_code=400, detail="No base timetable found.")

    engine = ReschedulingEngine(ds, t.get("assignments", []))
    res = engine.apply_disruptions([disruption], time_limit_seconds=20)

    is_feasible = (res.get("status") in ("OPTIMAL", "FEASIBLE"))
    validation = validate_hard_constraints(ds, res.get("schedule", [])) if is_feasible else {"is_valid": False}

    return {
        "success": is_feasible,
        "understood_intent": parsed_intent,
        "disruption": disruption,
        "solver_status": res.get("status"),
        "moved_count": res.get("moved_count", 0),
        "diff": res.get("diff", []),
        "proposed_schedule": res.get("schedule", []),
        "validation_passed": validation.get("is_valid", False),
        "llm_used": parsed_intent.get("llm_used", False)
    }
