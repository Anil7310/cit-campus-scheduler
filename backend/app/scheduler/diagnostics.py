from typing import Dict, List, Any
from app.scheduler.dataset_adapter import Dataset, Session, Room, Faculty, DAYS, TEACHING_PERIODS, PERIOD_INDEX, PERIODS
from app.scheduler.candidates import is_room_type_compatible

def diagnose_session_infeasibility(session: Session, dataset: Dataset, disruptions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes all possible (day, period, room) combinations for a session and
    counts how many were eliminated by each constraint family.
    """
    reasons_count = {
        "room_type_incompatible": 0,
        "insufficient_capacity": 0,
        "not_accessible": 0,
        "lunch_crossing": 0,
        "lab_window_violation": 0,
        "faculty_unavailable": 0,
        "room_maintenance": 0,
        "faculty_leave_disruption": 0,
        "room_closure_disruption": 0,
        "fixed_slot_conflict": 0
    }

    dur = session.duration_hours
    tot_students = sum(dataset.groups_by_id[gid].size for gid in session.student_groups if gid in dataset.groups_by_id)

    faculty_leaves = [
        (d.get("faculty_id"), d.get("day"), set(PERIODS[i] for i in range(PERIOD_INDEX.get(d.get("start_period"), 0), PERIOD_INDEX.get(d.get("end_period"), 0) + 1)))
        for d in disruptions if d.get("type") == "faculty_leave"
    ]
    room_closures = [
        (d.get("room_id"), d.get("day"), set(PERIODS[i] for i in range(PERIOD_INDEX.get(d.get("start_period"), 0), PERIOD_INDEX.get(d.get("end_period"), 0) + 1)))
        for d in disruptions if d.get("type") == "room_closure"
    ]

    total_combinations = len(DAYS) * len(TEACHING_PERIODS) * len(dataset.rooms)
    valid_slots = 0

    for day in DAYS:
        for p_idx, start_p in enumerate(TEACHING_PERIODS):
            if p_idx + dur > len(TEACHING_PERIODS):
                continue
            covered = [TEACHING_PERIODS[p_idx + i] for i in range(dur)]

            # Check fixed slot
            if session.fixed_slot:
                if session.fixed_slot.get("day") != day or session.fixed_slot.get("period") != start_p:
                    reasons_count["fixed_slot_conflict"] += len(dataset.rooms)
                    continue

            # Check lunch crossing
            if any(p in ["P1", "P2", "P3", "P4", "P5"] for p in covered) and any(p in ["P6", "P7", "P8", "P9"] for p in covered):
                reasons_count["lunch_crossing"] += len(dataset.rooms)
                continue

            # Check 3-hour lab window
            if session.session_type == "lab" and dur == 3:
                if covered != ["P2", "P3", "P4"] and covered != ["P6", "P7", "P8"]:
                    reasons_count["lab_window_violation"] += len(dataset.rooms)
                    continue

            # Check faculty static unavailability & leave
            fac_unavail = False
            fac_leave = False
            for fid in session.faculty_ids:
                fac = dataset.faculty_by_id.get(fid)
                if fac:
                    for un in fac.unavailability:
                        if un.get("day") == day and any(p in un.get("periods", []) for p in covered):
                            fac_unavail = True
                            break
                for lf_id, lf_day, lf_periods in faculty_leaves:
                    if fid == lf_id and day == lf_day and any(p in lf_periods for p in covered):
                        fac_leave = True
                        break

            if fac_unavail:
                reasons_count["faculty_unavailable"] += len(dataset.rooms)
                continue
            if fac_leave:
                reasons_count["faculty_leave_disruption"] += len(dataset.rooms)
                continue

            for room in dataset.rooms:
                if not is_room_type_compatible(session.required_room_type, room.type):
                    reasons_count["room_type_incompatible"] += 1
                    continue
                if room.capacity < tot_students:
                    reasons_count["insufficient_capacity"] += 1
                    continue
                if session.accessible_required and not room.accessible:
                    reasons_count["not_accessible"] += 1
                    continue

                # Room closure disruption
                r_closed = False
                for rc_id, rc_day, rc_periods in room_closures:
                    if room.id == rc_id and day == rc_day and any(p in rc_periods for p in covered):
                        r_closed = True
                        break
                if r_closed:
                    reasons_count["room_closure_disruption"] += 1
                    continue

                valid_slots += 1

    primary_blockers = [k for k, v in sorted(reasons_count.items(), key=lambda x: x[1], reverse=True) if v > 0]
    return {
        "session_id": session.id,
        "valid_candidate_slots": valid_slots,
        "primary_conflicting_constraints": primary_blockers[:3],
        "constraint_elimination_counts": reasons_count
    }
