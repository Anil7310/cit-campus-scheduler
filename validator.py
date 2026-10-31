"""
Official Timetable, Exam and Booking Validator for CIT
Usage:
    python validator.py cit_public.json schedule.json [schedule_base.json]
"""

import sys
import json
from typing import Dict, List, Any, Optional

PERIODS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11", "P12", "P13"]
TEACHING_PERIODS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]
PERIOD_INDEX = {p: i for i, p in enumerate(PERIODS)}

PERIOD_TIMES = {
    "P1": (8, 9), "P2": (9, 10), "P3": (10, 11), "P4": (11, 12), "P5": (12, 13),
    # Lunch 13:00 - 14:00
    "P6": (14, 15), "P7": (15, 16), "P8": (16, 17), "P9": (17, 18),
    # Evening events only
    "P10": (18, 19), "P11": (19, 20), "P12": (20, 21), "P13": (21, 22)
}

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

def validate_schedule(cit_data: Dict[str, Any], schedule_data: Dict[str, Any], schedule_base: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    hard_violations = []
    soft_penalties = {
        "faculty_avoid_penalty": 0,
        "group_gap_penalty": 0,
        "group_over_6h_penalty": 0,
        "two_lectures_same_day_penalty": 0,
        "room_under_utilization_penalty": 0,
        "p9_usage_penalty": 0,
        "total_soft_penalty": 0
    }
    
    rooms_by_id = {r["id"]: r for r in cit_data.get("rooms", [])}
    faculty_by_id = {f["id"]: f for f in cit_data.get("faculty", [])}
    groups_by_id = {g["id"]: g for g in cit_data.get("student_groups", [])}
    sessions_by_id = {s["id"]: s for s in cit_data.get("sessions", [])}
    for ns in schedule_data.get("new_sessions", []):
        if "id" in ns:
            sessions_by_id[ns["id"]] = ns
    for d in schedule_data.get("disruptions", []):
        if d.get("type") == "new_session" and "session" in d:
            ns = d["session"]
            if "id" in ns:
                sessions_by_id[ns["id"]] = ns
    exams_by_id = {e["id"]: e for e in cit_data.get("exams", [])}
    bookings_by_id = {b["id"]: b for b in cit_data.get("booking_requests", [])}

    assignments = schedule_data.get("timetable", [])
    exam_assignments = schedule_data.get("exams", [])
    booking_decisions = schedule_data.get("bookings", [])

    # 1. TIMETABLE VALIDATION
    assigned_session_ids = set()
    room_occupancy = {}    # (room_id, day, period) -> session_id
    faculty_occupancy = {} # (faculty_id, day, period) -> session_id
    group_occupancy = {}   # (group_id, day, period) -> list of (session_id, basket)
    faculty_daily_hours = {} # (faculty_id, day) -> total_hours
    group_daily_schedule = {} # (group_id, day) -> list of periods
    group_course_day = {} # (group_id, course_code, day) -> list of session_ids
    elective_basket_slots = {} # basket_slot_id -> (day, start_period)

    for item in assignments:
        sid = item.get("session_id")
        day = item.get("day")
        start_period = item.get("start_period")
        room_id = item.get("room_id")

        if not sid or sid not in sessions_by_id:
            hard_violations.append(f"Invalid or missing session_id: {sid}")
            continue

        if sid in assigned_session_ids:
            hard_violations.append(f"Session {sid} is scheduled more than once.")
        assigned_session_ids.add(sid)

        session = sessions_by_id[sid]
        duration = session.get("duration_hours", 1)

        if day not in DAYS:
            hard_violations.append(f"Session {sid} scheduled on invalid day: {day}")

        if start_period not in PERIOD_INDEX:
            hard_violations.append(f"Session {sid} scheduled with invalid start_period: {start_period}")
            continue

        start_idx = PERIOD_INDEX[start_period]
        covered_periods = [PERIODS[start_idx + i] for i in range(duration) if start_idx + i < len(PERIODS)]

        # Check lunch crossing (lunch is between P5 and P6)
        if any(p in ["P1", "P2", "P3", "P4", "P5"] for p in covered_periods) and any(p in ["P6", "P7", "P8", "P9"] for p in covered_periods):
            hard_violations.append(f"Session {sid} crosses lunch break: {covered_periods}")

        # Check 3-hour labs only in P2-P4 or P6-P8
        if session.get("session_type") == "lab" and duration == 3:
            if covered_periods != ["P2", "P3", "P4"] and covered_periods != ["P6", "P7", "P8"]:
                hard_violations.append(f"3-hour lab session {sid} must only run in P2-P4 or P6-P8, but got {covered_periods}")

        # Check Fixed Slot
        fixed = session.get("fixed_slot")
        if fixed:
            if fixed.get("day") != day or fixed.get("period") != start_period:
                hard_violations.append(f"Session {sid} has fixed slot {fixed} but was scheduled at {day} {start_period}")

        # Room checks
        if room_id not in rooms_by_id:
            hard_violations.append(f"Session {sid} assigned to non-existent room: {room_id}")
            continue

        room = rooms_by_id[room_id]
        
        # Room Type Check
        req_type = session.get("required_room_type")
        if req_type and room.get("type") != req_type:
            # Allow classroom session in lecture hall if capacity allows, but lab requires exact lab type
            if "lab" in req_type or "theatre" in req_type or "auditorium" in req_type:
                hard_violations.append(f"Session {sid} requires room type '{req_type}' but assigned room {room_id} is of type '{room.get('type')}'")
            elif req_type == "classroom" and room.get("type") not in ["classroom", "lecture_hall"]:
                hard_violations.append(f"Session {sid} requires '{req_type}' but assigned room {room_id} is '{room.get('type')}'")

        # Capacity Check
        total_students = sum(groups_by_id[gid]["size"] for gid in session.get("student_groups", []) if gid in groups_by_id)
        if room.get("capacity", 0) < total_students:
            hard_violations.append(f"Room {room_id} capacity ({room.get('capacity')}) is smaller than session {sid} size ({total_students})")

        # Accessibility Check
        if session.get("accessible_required") and not room.get("accessible"):
            hard_violations.append(f"Session {sid} requires an accessible room, but room {room_id} is not accessible")

        # Room Maintenance Check
        for m in room.get("maintenance_windows", []):
            if m.get("day") == day:
                m_start = PERIOD_INDEX.get(m.get("start_period"), -1)
                m_end = PERIOD_INDEX.get(m.get("end_period"), -1)
                for p in covered_periods:
                    p_idx = PERIOD_INDEX.get(p, -1)
                    if m_start <= p_idx <= m_end:
                        hard_violations.append(f"Room {room_id} is under maintenance during {day} {p} (session {sid})")

        # Room overlap check
        for p in covered_periods:
            key = (room_id, day, p)
            if key in room_occupancy:
                hard_violations.append(f"Room clash: Room {room_id} has both {room_occupancy[key]} and {sid} at {day} {p}")
            else:
                room_occupancy[key] = sid

        # Faculty checks
        for fid in session.get("faculty_ids", []):
            fac = faculty_by_id.get(fid)
            if not fac:
                hard_violations.append(f"Session {sid} references unknown faculty: {fid}")
                continue

            # Faculty Unavailability
            for un in fac.get("unavailability", []):
                if un.get("day") == day and any(p in un.get("periods", []) for p in covered_periods):
                    hard_violations.append(f"Faculty {fid} is unavailable on {day} during {covered_periods} (session {sid})")

            # Faculty Overlap
            for p in covered_periods:
                fkey = (fid, day, p)
                if fkey in faculty_occupancy:
                    hard_violations.append(f"Faculty clash: Faculty {fid} is assigned to both {faculty_occupancy[fkey]} and {sid} at {day} {p}")
                else:
                    faculty_occupancy[fkey] = sid

            # Faculty daily limit
            fd_key = (fid, day)
            faculty_daily_hours[fd_key] = faculty_daily_hours.get(fd_key, 0) + duration

            # Soft: Faculty avoid periods
            for p in covered_periods:
                if p in fac.get("avoid_periods", []):
                    soft_penalties["faculty_avoid_penalty"] += 5

        # Student Group checks
        basket = session.get("elective_basket")
        for gid in session.get("student_groups", []):
            for p in covered_periods:
                gkey = (gid, day, p)
                if gkey in group_occupancy:
                    # If both are in the same elective basket, it's allowed!
                    clashing_sessions = group_occupancy[gkey]
                    can_share = all(b is not None and b == basket for (_, b) in clashing_sessions)
                    if not can_share:
                        hard_violations.append(f"Student group clash: Group {gid} has multiple sessions at {day} {p}: {[s for s, _ in clashing_sessions]} and {sid}")
                    clashing_sessions.append((sid, basket))
                else:
                    group_occupancy[gkey] = [(sid, basket)]

            gd_key = (gid, day)
            if gd_key not in group_daily_schedule:
                group_daily_schedule[gd_key] = []
            group_daily_schedule[gd_key].extend(covered_periods)

            # Course same day check
            ccode = session.get("course_code")
            gcd_key = (gid, ccode, day)
            if gcd_key not in group_course_day:
                group_course_day[gcd_key] = []
            group_course_day[gcd_key].append(sid)

        # Elective Basket synchronization
        if basket:
            if basket not in elective_basket_slots:
                elective_basket_slots[basket] = (day, start_period)
            else:
                expected_day, expected_period = elective_basket_slots[basket]
                if day != expected_day or start_period != expected_period:
                    hard_violations.append(f"Elective basket {basket} sessions must run at the same time: {sid} is at {day} {start_period}, expected {expected_day} {expected_period}")

        # Soft penalties
        # P9 penalty
        if "P9" in covered_periods:
            soft_penalties["p9_usage_penalty"] += 6

        # Room under-utilization (<40% of room capacity)
        if room.get("capacity", 0) > 0:
            util = total_students / room.get("capacity")
            if util < 0.40:
                soft_penalties["room_under_utilization_penalty"] += 4

    # Check that all sessions were scheduled
    missing_sessions = set(sessions_by_id.keys()) - assigned_session_ids
    if missing_sessions:
        hard_violations.append(f"Unscheduled sessions count: {len(missing_sessions)}. Missing IDs: {list(missing_sessions)[:5]}")

    # Faculty daily limit check
    for (fid, day), total_h in faculty_daily_hours.items():
        limit = faculty_by_id[fid].get("daily_limit_hours", 4)
        if total_h > limit:
            hard_violations.append(f"Faculty {fid} exceeded daily teaching limit on {day}: {total_h} hours (limit {limit})")

    # Group daily gaps and >6 hours soft penalties
    for (gid, day), p_list in group_daily_schedule.items():
        unique_indices = sorted(list(set(PERIOD_INDEX[p] for p in p_list if p in TEACHING_PERIODS)))
        if len(unique_indices) > 6:
            soft_penalties["group_over_6h_penalty"] += (len(unique_indices) - 6) * 10

        # Gaps (excluding lunch gap between P5 and P6)
        for i in range(len(unique_indices) - 1):
            curr_p = unique_indices[i]
            next_p = unique_indices[i+1]
            diff = next_p - curr_p
            if diff > 1:
                # If gap is strictly P5 (index 4) to P6 (index 5), diff is 1, so no gap.
                # If gap spans across other periods, penalize free periods
                free_periods = diff - 1
                # If it spans across lunch (between 4 and 5), subtract 1
                if curr_p <= 4 and next_p >= 5:
                    free_periods = max(0, free_periods - 1)
                soft_penalties["group_gap_penalty"] += free_periods * 3

    # Group two lectures of same course on same day penalty
    for (gid, ccode, day), s_list in group_course_day.items():
        lec_count = sum(1 for sid in s_list if sessions_by_id[sid].get("session_type") == "lecture")
        if lec_count > 1:
            soft_penalties["two_lectures_same_day_penalty"] += (lec_count - 1) * 8

    soft_penalties["total_soft_penalty"] = sum(v for k, v in soft_penalties.items() if k != "total_soft_penalty")

    # 2. EXAM VALIDATION (Capacity halved, group conflicts, room conflicts)
    exam_room_occ = {}
    exam_group_occ = {}
    for ex in exam_assignments:
        eid = ex.get("exam_id")
        day = ex.get("day")
        start_period = ex.get("start_period")
        room_ids = ex.get("room_ids", [])
        if isinstance(room_ids, str):
            room_ids = [room_ids]

        if eid not in exams_by_id:
            hard_violations.append(f"Invalid exam_id: {eid}")
            continue

        exam_obj = exams_by_id[eid]
        students = exam_obj.get("student_count", 0)
        dur = exam_obj.get("duration_hours", 2)
        s_idx = PERIOD_INDEX.get(start_period, 0)
        cov = [PERIODS[s_idx + i] for i in range(dur) if s_idx + i < len(PERIODS)]

        # Effective room capacity is halved
        effective_cap = sum(rooms_by_id[rid].get("capacity", 0) // 2 for rid in room_ids if rid in rooms_by_id)
        if effective_cap < students:
            hard_violations.append(f"Exam {eid} effective capacity check failed: Need {students}, allocated rooms {room_ids} provide effective capacity {effective_cap} (halved)")

        for rid in room_ids:
            for p in cov:
                k = (rid, day, p)
                if k in exam_room_occ:
                    hard_violations.append(f"Exam room clash: Room {rid} has multiple exams at {day} {p}")
                exam_room_occ[k] = eid

        for gid in exam_obj.get("student_groups", []):
            for p in cov:
                gk = (gid, day, p)
                if gk in exam_group_occ:
                    hard_violations.append(f"Exam student group clash: Group {gid} has multiple exams at {day} {p}")
                exam_group_occ[gk] = eid

    # 3. BOOKING SCORING & VALIDATION
    booking_score = 0
    approved_bookings_count = 0
    rejected_bookings_count = 0
    alternatives_count = 0

    for b_dec in booking_decisions:
        bid = b_dec.get("booking_id")
        decision = b_dec.get("decision")
        assigned_room = b_dec.get("assigned_room")
        reason = b_dec.get("reason", "")
        
        req = bookings_by_id.get(bid)
        if not req:
            continue

        if req.get("status") == "cancelled":
            if decision == "approved":
                hard_violations.append(f"Booking {bid} was cancelled by requester but was approved!")
            else:
                booking_score += 5
            continue

        day = b_dec.get("day", req.get("day"))
        start_period = b_dec.get("start_period", req.get("start_period"))
        end_period = b_dec.get("end_period", req.get("end_period"))
        s_i = PERIOD_INDEX.get(start_period, 0)
        e_i = PERIOD_INDEX.get(end_period, s_i)
        cov = [PERIODS[i] for i in range(s_i, e_i + 1)]

        if decision == "approved":
            approved_bookings_count += 1
            # Check clash with regular timetable sessions
            for p in cov:
                k = (assigned_room, day, p)
                if k in room_occupancy:
                    hard_violations.append(f"Booking {bid} clash: Room {assigned_room} is occupied by class session {room_occupancy[k]} at {day} {p}")
                    booking_score -= 50
                else:
                    booking_score += 10
        elif decision == "alternative_offered":
            alternatives_count += 1
            booking_score += 7
        elif decision == "rejected":
            rejected_bookings_count += 1
            if reason:
                booking_score += 5
            else:
                booking_score += 2

    # 4. RESCHEDULING / MOVED SESSIONS COUNT (if base schedule is provided)
    moved_count = 0
    if schedule_base:
        base_map = {item["session_id"]: (item.get("day"), item.get("start_period"), item.get("room_id")) 
                    for item in schedule_base.get("timetable", [])}
        for item in assignments:
            sid = item.get("session_id")
            new_val = (item.get("day"), item.get("start_period"), item.get("room_id"))
            if sid in base_map and base_map[sid] != new_val:
                moved_count += 1

    return {
        "is_valid": len(hard_violations) == 0,
        "hard_violations_count": len(hard_violations),
        "hard_violations": hard_violations,
        "soft_penalties": soft_penalties,
        "booking_score": booking_score,
        "moved_sessions_count": moved_count,
        "stats": {
            "total_sessions_assigned": len(assignments),
            "total_exams_assigned": len(exam_assignments),
            "approved_bookings": approved_bookings_count,
            "rejected_bookings": rejected_bookings_count,
            "alternatives_offered": alternatives_count
        }
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python validator.py cit_public.json schedule.json [schedule_base.json]")
        sys.exit(1)

    cit_path = sys.argv[1]
    schedule_path = sys.argv[2]
    base_path = sys.argv[3] if len(sys.argv) > 3 else None

    with open(cit_path, "r", encoding="utf-8") as f:
        cit_data = json.load(f)

    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule_data = json.load(f)

    schedule_base = None
    if base_path:
        with open(base_path, "r", encoding="utf-8") as f:
            schedule_base = json.load(f)

    result = validate_schedule(cit_data, schedule_data, schedule_base)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["is_valid"] else 1)
