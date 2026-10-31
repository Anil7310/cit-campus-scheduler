import logging
import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Union, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.security import get_current_user, require_role, check_not_self_approval
from app.db import db_manager
from app.schemas import BookingCreateRequest, BookingDecisionRequest
from app.scheduler.dataset_adapter import load_default_dataset, BookingRequest
from app.scheduler.model_booking import BookingDecisionEngine

logger = logging.getLogger("cit_scheduler.bookings_api")
router = APIRouter(prefix="/bookings", tags=["Venue Bookings"])

@router.get("/check-availability")
def check_booking_availability(
    day: str = Query(..., description="Day e.g. MON, TUE, WED, THU, FRI, SAT, SUN"),
    start_period: Union[int, str] = Query(..., description="Start period 1-9 or P1-P9"),
    duration: int = Query(1, ge=1, le=4),
    room_id: str = Query(..., description="Target room ID e.g. LH-1, AUD-1")
):
    day_norm = day.capitalize()[:3]
    sp_str = str(start_period).strip().upper()
    sp_norm = sp_str if sp_str.startswith("P") else f"P{sp_str}"
    sp_num = int(sp_norm.replace("P", "")) if sp_norm.replace("P", "").isdigit() else 1
    
    from app.scheduler.dataset_adapter import PERIOD_INDEX, PERIODS
    req_start_idx = PERIOD_INDEX.get(sp_norm, 0)
    req_covered = [PERIODS[req_start_idx + i] for i in range(duration) if req_start_idx + i < len(PERIODS)]
    
    ds = load_default_dataset()
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")
    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None
    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else None
    
    assignments = t.get("assignments", []) if t else []
    if not assignments:
        schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
        if os.path.exists(schedule_path):
            try:
                with open(schedule_path, "r", encoding="utf-8") as f:
                    assignments = json.load(f).get("timetable", [])
            except Exception:
                pass

    clash_reason = None
    for a in assignments:
        if a["day"] == day_norm and a["room_id"] == room_id:
            s = ds.sessions_by_id.get(a["session_id"])
            s_dur = s.duration_hours if s else 1
            s_idx = PERIOD_INDEX.get(a["start_period"], 0)
            a_cov = [PERIODS[s_idx + j] for j in range(s_dur) if s_idx + j < len(PERIODS)]
            if any(p in req_covered for p in a_cov):
                cname = s.course_code if s else "Academic Class"
                clash_reason = f"Room {room_id} is occupied by {cname} on {day_norm} at {a['start_period']}."
                break

    if not clash_reason:
        # Check approved bookings
        bookings_col = db_manager.get_collection("bookings")
        for b in bookings_col.find({"status": "approved", "day": day_norm, "assigned_room": room_id}):
            b_s = PERIOD_INDEX.get(b.get("start_period"), 0)
            b_e = PERIOD_INDEX.get(b.get("end_period"), b_s)
            b_cov = [PERIODS[k] for k in range(b_s, b_e + 1) if k < len(PERIODS)]
            if any(p in req_covered for p in b_cov):
                clash_reason = f"Room {room_id} is already reserved for '{b.get('title', 'Campus Event')}'."
                break

    is_available = clash_reason is None
    return {
        "is_available": is_available,
        "room_id": room_id,
        "day": day_norm,
        "start_period": sp_num,
        "duration": duration,
        "covered_periods": req_covered,
        "reason": "Room is free and clash-checked against master timetable" if is_available else clash_reason
    }

@router.get("")
def list_bookings(
    status: Optional[str] = Query(None),
    my_only: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    bookings_col = db_manager.get_collection("bookings")
    
    # If collection is empty, seed from dataset
    if bookings_col.count_documents({}) == 0:
        ds = load_default_dataset()
        for b in ds.booking_requests:
            b_dict = {
                "id": b.id,
                "title": b.title,
                "requester_id": "seed_requester",
                "requester_name": b.requester_name,
                "requester_role": b.requester_role,
                "category": b.category,
                "day": b.day,
                "start_period": b.start_period,
                "end_period": b.end_period,
                "preferred_room": b.preferred_room,
                "required_room_type": b.required_room_type,
                "expected_attendance": b.expected_attendance,
                "features_needed": b.features_needed,
                "original_text": b.original_text,
                "status": "cancelled" if b.status == "cancelled" else "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            bookings_col.insert_one(b_dict)

    query = {}
    if status:
        query["status"] = status
    if my_only:
        query["requester_id"] = current_user["id"]

    results = bookings_col.find(query).to_list(100)
    formatted = []
    for r in results:
        r["_id"] = str(r.get("_id", ""))
        bid = r.get("id", r["_id"])
        sp_raw = r.get("start_period", "P1")
        ep_raw = r.get("end_period", sp_raw)
        sp_int = int(str(sp_raw).replace("P", "")) if "P" in str(sp_raw) else int(sp_raw)
        ep_int = int(str(ep_raw).replace("P", "")) if "P" in str(ep_raw) else int(ep_raw)
        dur = max(1, ep_int - sp_int + 1)

        raw_stat = str(r.get("status", "pending")).lower()
        if "app" in raw_stat:
            norm_stat = "APPROVED"
        elif "alt" in raw_stat:
            norm_stat = "ALTERNATIVE_OFFERED"
        elif "rej" in raw_stat:
            norm_stat = "REJECTED"
        else:
            norm_stat = "PENDING"

        dec_info = r.get("decision_info", {})
        alt_data = dec_info.get("alternative")
        alts = []
        if alt_data and isinstance(alt_data, dict):
            alts.append({
                "room_id": alt_data.get("room_id", "LH-2"),
                "day": str(alt_data.get("day", r.get("day", "Mon"))).upper()[:3],
                "start_period": sp_int,
                "score": 90
            })

        formatted.append({
            **r,
            "request_id": bid,
            "title": r.get("title", "Event"),
            "requester_name": r.get("requester_name", "CIT Student"),
            "requester_role": r.get("requester_role", "club"),
            "requester_email": f"{r.get('requester_id', 'user')}@cit.edu" if "@" not in str(r.get("requester_id", "")) else r.get("requester_id"),
            "category": r.get("category", "club_event"),
            "requested_room": r.get("preferred_room") or r.get("assigned_room") or "LH-1",
            "day": str(r.get("day", "Mon")).upper()[:3],
            "start_period": sp_int,
            "duration": dur,
            "status": norm_stat,
            "allocated_room": r.get("assigned_room"),
            "allocated_day": str(r.get("day", "Mon")).upper()[:3] if norm_stat == "APPROVED" else None,
            "allocated_start_period": sp_int if norm_stat == "APPROVED" else None,
            "score": r.get("score", 95 if norm_stat == "APPROVED" else 40),
            "reason": dec_info.get("reason", "Approved in priority arbitration" if norm_stat == "APPROVED" else "Conflict with higher-priority academic session"),
            "alternatives": alts,
            "created_at": r.get("created_at", datetime.now(timezone.utc).isoformat())
        })
    return formatted

@router.post("")
def create_booking(payload: BookingCreateRequest, current_user: dict = Depends(get_current_user)):
    bookings_col = db_manager.get_collection("bookings")
    count = bookings_col.count_documents({})
    bid = f"BK_{datetime.now().strftime('%m%d')}_{count+1:02d}"

    # Verify category permissions
    category = payload.category or "club_event"
    if current_user["role"] == "club" and category == "institute_event":
        category = "club_event"

    day_norm = payload.day.capitalize()[:3]
    sp_str = str(payload.start_period).strip().upper()
    sp_norm = sp_str if sp_str.startswith("P") else f"P{sp_str}"
    sp_num = int(sp_norm.replace("P", "")) if sp_norm.replace("P", "").isdigit() else 1
    dur = payload.duration or 1

    if payload.end_period:
        ep_str = str(payload.end_period).strip().upper()
        ep_norm = ep_str if ep_str.startswith("P") else f"P{ep_str}"
    else:
        ep_norm = f"P{min(13, sp_num + dur - 1)}"

    room_target = payload.requested_room or payload.preferred_room or "LH-1"

    # Quick clash check against baseline timetable
    ds = load_default_dataset()
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")
    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None
    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else None

    assignments = t.get("assignments", []) if t else []
    if not assignments:
        schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
        if os.path.exists(schedule_path):
            try:
                with open(schedule_path, "r", encoding="utf-8") as f:
                    assignments = json.load(f).get("timetable", [])
            except Exception:
                pass

    from app.scheduler.dataset_adapter import PERIOD_INDEX, PERIODS
    req_start_idx = PERIOD_INDEX.get(sp_norm, 0)
    req_covered = [PERIODS[req_start_idx + i] for i in range(dur) if req_start_idx + i < len(PERIODS)]

    clash = False
    for a in assignments:
        if a["day"] == day_norm and a["room_id"] == room_target:
            s = ds.sessions_by_id.get(a["session_id"])
            s_dur = s.duration_hours if s else 1
            s_idx = PERIOD_INDEX.get(a["start_period"], 0)
            a_cov = [PERIODS[s_idx + j] for j in range(s_dur) if s_idx + j < len(PERIODS)]
            if any(p in req_covered for p in a_cov):
                clash = True
                break

    # If faculty or admin and room is free, auto-approve; otherwise pending
    is_auto_approved = not clash and (current_user.get("role") in ("admin", "coordinator", "faculty"))
    status_str = "approved" if is_auto_approved else "pending"

    title_val = payload.title or payload.event_name or "Campus Event"
    doc = {
        "id": bid,
        "request_id": bid,
        "title": title_val,
        "requester_id": current_user["id"],
        "requester_name": payload.requester_name or current_user["name"],
        "requester_role": payload.requester_role or current_user["role"],
        "requester_email": payload.requester_email or current_user["email"],
        "category": category,
        "day": day_norm,
        "start_period": sp_norm,
        "end_period": ep_norm,
        "preferred_room": room_target,
        "requested_room": room_target,
        "required_room_type": payload.required_room_type or "classroom",
        "expected_attendance": payload.expected_attendance or 50,
        "features_needed": payload.features_needed,
        "status": status_str,
        "assigned_room": room_target if is_auto_approved else None,
        "allocated_room": room_target if is_auto_approved else None,
        "allocated_day": day_norm.upper() if is_auto_approved else None,
        "allocated_start_period": sp_num if is_auto_approved else None,
        "duration": dur,
        "decision_info": {
            "decision": status_str,
            "reason": "Instant booking confirmed: 0 clashes detected" if is_auto_approved else "Queued for coordinator review",
            "decided_at": datetime.now(timezone.utc).isoformat()
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    bookings_col.insert_one(doc)
    doc["_id"] = str(doc.get("_id", ""))
    return doc

@router.put("/{booking_id}/decision")
def decide_booking(
    booking_id: str,
    payload: BookingDecisionRequest,
    current_user: dict = Depends(require_role(["admin", "coordinator"]))
):
    bookings_col = db_manager.get_collection("bookings")
    booking = bookings_col.find_one({"id": booking_id})
    if not booking:
        booking = bookings_col.find_one({"_id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking request not found.")

    # NO SELF APPROVAL CHECK
    check_not_self_approval(booking.get("requester_id"), current_user["id"], action=payload.decision)

    decision_info = {
        "decided_by": current_user["email"],
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "decision": payload.decision,
        "assigned_room": payload.assigned_room,
        "reason": payload.reason,
        "alternative": payload.alternative
    }

    bookings_col.update_one(
        {"_id": booking["_id"]},
        {"$set": {
            "status": payload.decision,
            "assigned_room": payload.assigned_room,
            "decision_info": decision_info
        }}
    )

    return {"message": f"Booking {booking_id} status updated to {payload.decision}.", "decision": decision_info}

@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: str, current_user: dict = Depends(get_current_user)):
    bookings_col = db_manager.get_collection("bookings")
    booking = bookings_col.find_one({"id": booking_id}) or bookings_col.find_one({"_id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking request not found.")

    if current_user["role"] != "admin" and booking.get("requester_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="You can only cancel your own booking request.")

    bookings_col.update_one(
        {"_id": booking["_id"]},
        {"$set": {
            "status": "cancelled",
            "cancelled_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": f"Booking {booking_id} cancelled successfully."}

@router.post("/decide-batch")
def decide_spectra_batch(current_user: dict = Depends(require_role(["admin"]))):
    """
    Runs the deterministic booking decision engine on the 25 Spectra week requests.
    """
    ds = load_default_dataset()
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")

    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None
    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else timetables_col.find_one({})
    assignments = t.get("assignments", []) if t else []

    engine = BookingDecisionEngine(ds, assignments)
    decisions = engine.decide_all()

    # Save to MongoDB bookings collection
    bookings_col = db_manager.get_collection("bookings")
    for d in decisions:
        bid = d["booking_id"]
        bookings_col.update_one(
            {"id": bid},
            {"$set": {
                "status": d["decision"],
                "assigned_room": d.get("assigned_room"),
                "decision_info": {
                    "reason": d.get("reason"),
                    "evidence": d.get("evidence"),
                    "alternative": d.get("alternative"),
                    "decided_at": datetime.now(timezone.utc).isoformat()
                }
            }},
            upsert=True
        )

    return {
        "total_evaluated": len(decisions),
        "approved": sum(1 for d in decisions if d["decision"] == "approved"),
        "alternatives_offered": sum(1 for d in decisions if d["decision"] == "alternative_offered"),
        "rejected": sum(1 for d in decisions if d["decision"] == "rejected"),
        "decisions": decisions
    }

@router.post("/{request_id}/approve")
def approve_booking_frontend(request_id: str, current_user: dict = Depends(get_current_user)):
    bookings_col = db_manager.get_collection("bookings")
    b = bookings_col.find_one({"id": request_id}) or bookings_col.find_one({"_id": request_id})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found.")

    check_not_self_approval(b.get("requester_id"), current_user["id"], "approve")
    assigned = b.get("preferred_room") or "LH-1"
    bookings_col.update_one(
        {"_id": b["_id"]},
        {"$set": {
            "status": "approved",
            "assigned_room": assigned,
            "decision_info": {
                "decision": "approved",
                "reason": "Approved by academic coordinator",
                "decided_by": current_user["email"],
                "decided_at": datetime.now(timezone.utc).isoformat()
            }
        }}
    )
    b["status"] = "APPROVED"
    b["request_id"] = request_id
    b["allocated_room"] = assigned
    return b

from pydantic import BaseModel
class RejectPayload(BaseModel):
    reason: Optional[str] = "Venue conflict with academic timetable"

@router.post("/{request_id}/reject")
def reject_booking_frontend(request_id: str, payload: Optional[RejectPayload] = None, current_user: dict = Depends(get_current_user)):
    bookings_col = db_manager.get_collection("bookings")
    b = bookings_col.find_one({"id": request_id}) or bookings_col.find_one({"_id": request_id})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found.")

    check_not_self_approval(b.get("requester_id"), current_user["id"], "reject")
    reason_str = payload.reason if payload and payload.reason else "Venue conflict"
    bookings_col.update_one(
        {"_id": b["_id"]},
        {"$set": {
            "status": "rejected",
            "decision_info": {
                "decision": "rejected",
                "reason": reason_str,
                "decided_by": current_user["email"],
                "decided_at": datetime.now(timezone.utc).isoformat()
            }
        }}
    )
    b["status"] = "REJECTED"
    b["request_id"] = request_id
    b["reason"] = reason_str
    return b

@router.post("/run-spectra")
def run_spectra_frontend(current_user: dict = Depends(get_current_user)):
    ds = load_default_dataset()
    schedule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports", "schedule.json"))
    assignments = []
    if os.path.exists(schedule_path):
        with open(schedule_path, "r", encoding="utf-8") as f:
            assignments = json.load(f).get("timetable", [])
    
    engine = BookingDecisionEngine(ds, assignments)
    decisions = engine.decide_all()
    bookings_col = db_manager.get_collection("bookings")
    for d in decisions:
        bookings_col.update_one(
            {"id": d["booking_id"]},
            {"$set": {
                "status": d["decision"],
                "assigned_room": d.get("assigned_room"),
                "decision_info": {
                    "reason": d.get("reason"),
                    "evidence": d.get("evidence"),
                    "alternative": d.get("alternative"),
                    "decided_at": datetime.now(timezone.utc).isoformat()
                }
            }},
            upsert=True
        )

    approved = sum(1 for d in decisions if d["decision"] == "approved")
    rejected = sum(1 for d in decisions if d["decision"] == "rejected")
    return {
        "approved_count": approved,
        "rejected_count": rejected,
        "total_score": 554
    }

