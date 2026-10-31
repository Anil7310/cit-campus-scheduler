from typing import Dict, Any, List
from app.scheduler.dataset_adapter import Dataset, Session, Room, Faculty, DAYS, TEACHING_PERIODS, PERIOD_INDEX, PERIODS
from app.scheduler.candidates import generate_candidates_for_session

def generate_session_explanation(session_id: str, timetable_assignments: List[Dict[str, Any]], dataset: Dataset) -> Dict[str, Any]:
    session = dataset.sessions_by_id.get(session_id)
    if not session:
        return {"error": f"Session {session_id} not found."}

    # Find the session's assignment
    assigned_item = next((a for a in timetable_assignments if a.get("session_id") == session_id), None)
    if not assigned_item:
        return {"error": f"Session {session_id} has not been scheduled."}

    day = assigned_item["day"]
    start_period = assigned_item["start_period"]
    room_id = assigned_item["room_id"]
    room = dataset.rooms_by_id.get(room_id)

    # Re-evaluate all potential candidates
    candidates = generate_candidates_for_session(session, dataset)
    chosen_candidate = next((c for c in candidates if c.day == day and c.start_period == start_period and c.room_id == room_id), None)

    # Determine why this slot and room were picked
    reasons = []
    reasons.append(f"Venue {room.name} ({room_id}) was selected because it matches required type '{session.required_room_type}' and satisfies student cohort capacity ({room.capacity} >= {sum(dataset.groups_by_id[g].size for g in session.student_groups)}).")

    if session.session_type == "lab" and session.duration_hours == 3:
        reasons.append(f"As a 3-hour laboratory session, it was restricted to legal CIT lab windows (P2-P4 or P6-P8) to avoid crossing the mandatory 13:00-14:00 lunch break.")

    if session.fixed_slot:
        reasons.append(f"This session had a fixed slot constraint locking it strictly to {session.fixed_slot['day']} {session.fixed_slot['period']}.")

    # Faculty reasons
    for fid in session.faculty_ids:
        fac = dataset.faculty_by_id.get(fid)
        if fac:
            unavail_periods = [f"{u['day']} {','.join(u['periods'])}" for u in fac.unavailability]
            if unavail_periods:
                reasons.append(f"Instructor {fac.name} ({fid}) has known unavailability ({'; '.join(unavail_periods)}), eliminating alternate slots.")

    cost_breakdown = {
        "candidate_soft_cost": chosen_candidate.soft_cost if chosen_candidate else 0,
        "p9_penalty": 6 if start_period == "P9" else 0,
        "is_accessible": room.accessible if room else False,
        "capacity_utilization": f"{(sum(dataset.groups_by_id[g].size for g in session.student_groups) / room.capacity * 100):.1f}%" if room else "N/A"
    }

    evidence_summary = (
        f"Session {session.course_code} ({session.id}) was placed on {day} at {start_period} in {room.name} "
        f"after exploring {len(candidates)} valid candidate permutations. "
        + " ".join(reasons)
    )

    return {
        "session_id": session_id,
        "course_code": session.course_code,
        "session_type": session.session_type,
        "assigned_day": day,
        "assigned_period": start_period,
        "assigned_room": room.name if room else room_id,
        "total_legal_candidates_evaluated": len(candidates),
        "cost_breakdown": cost_breakdown,
        "decision_rationale": reasons,
        "explanation_text": evidence_summary
    }
