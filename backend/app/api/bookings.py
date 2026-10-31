import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.security import get_current_user, require_role, check_not_self_approval
from app.db import db_manager
from app.schemas import BookingCreateRequest, BookingDecisionRequest
from app.scheduler.dataset_adapter import load_default_dataset, BookingRequest
from app.scheduler.model_booking import BookingDecisionEngine

logger = logging.getLogger("cit_scheduler.bookings_api")
router = APIRouter(prefix="/bookings", tags=["Venue Bookings"])

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
    for r in results:
        r["_id"] = str(r.get("_id", ""))
    return results

@router.post("")
def create_booking(payload: BookingCreateRequest, current_user: dict = Depends(get_current_user)):
    bookings_col = db_manager.get_collection("bookings")
    count = bookings_col.count_documents({})
    bid = f"BK_{datetime.now().strftime('%m%d')}_{count+1:02d}"

    # Verify category permissions
    category = payload.category
    if current_user["role"] == "club" and category == "institute_event":
        category = "club_event"

    doc = {
        "id": bid,
        "title": payload.title,
        "requester_id": current_user["id"],
        "requester_name": current_user["name"],
        "requester_role": current_user["role"],
        "category": category,
        "day": payload.day,
        "start_period": payload.start_period,
        "end_period": payload.end_period,
        "preferred_room": payload.preferred_room,
        "required_room_type": payload.required_room_type,
        "expected_attendance": payload.expected_attendance,
        "features_needed": payload.features_needed,
        "original_text": payload.original_text,
        "status": "pending",
        "decision": None,
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
