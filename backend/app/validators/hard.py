from typing import Dict, List, Any
from app.scheduler.dataset_adapter import Dataset, PERIODS, TEACHING_PERIODS, PERIOD_INDEX, DAYS
from app.scheduler.candidates import is_room_type_compatible

def validate_hard_constraints(dataset: Dataset, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
    violations = []
    assigned_session_ids = set()
    room_occupancy = {}
    faculty_occupancy = {}
    group_occupancy = {}
    faculty_daily_hours = {}
    basket_slots = {}

    sessions_by_id = dataset.sessions_by_id
    rooms_by_id = dataset.rooms_by_id
    groups_by_id = dataset.groups_by_id
    faculty_by_id = dataset.faculty_by_id

    for item in assignments:
        sid = item.get("session_id")
        day = item.get("day")
        start_period = item.get("start_period")
        room_id = item.get("room_id")

        if not sid or sid not in sessions_by_id:
            violations.append(f"Invalid session id: {sid}")
            continue

        if sid in assigned_session_ids:
            violations.append(f"Session {sid} scheduled multiple times.")
        assigned_session_ids.add(sid)

        s = sessions_by_id[sid]
        dur = s.duration_hours

        if day not in DAYS:
            violations.append(f"Session {sid} has invalid day: {day}")

        if start_period not in PERIOD_INDEX:
            violations.append(f"Session {sid} has invalid start period: {start_period}")
            continue

        s_idx = PERIOD_INDEX[start_period]
        covered = [PERIODS[s_idx + i] for i in range(dur) if s_idx + i < len(PERIODS)]

        # Lunch break check
        if any(p in ["P1", "P2", "P3", "P4", "P5"] for p in covered) and any(p in ["P6", "P7", "P8", "P9"] for p in covered):
            violations.append(f"Session {sid} crosses lunch break: {covered}")

        # 3-hour lab check
        if s.session_type == "lab" and dur == 3:
            if covered != ["P2", "P3", "P4"] and covered != ["P6", "P7", "P8"]:
                violations.append(f"3-hour lab {sid} must only run in P2-P4 or P6-P8, but is at {covered}")

        # Fixed slot check
        if s.fixed_slot:
            if s.fixed_slot.get("day") != day or s.fixed_slot.get("period") != start_period:
                violations.append(f"Session {sid} fixed slot violated: expected {s.fixed_slot}, got {day} {start_period}")

        # Room checks
        if room_id not in rooms_by_id:
            violations.append(f"Session {sid} assigned to unknown room: {room_id}")
            continue

        room = rooms_by_id[room_id]
        if not is_room_type_compatible(s.required_room_type, room.type):
            violations.append(f"Session {sid} requires room type '{s.required_room_type}' but room {room_id} is '{room.type}'")

        tot_students = sum(groups_by_id[gid].size for gid in s.student_groups if gid in groups_by_id)
        if room.capacity < tot_students:
            violations.append(f"Room {room_id} capacity ({room.capacity}) < session {sid} size ({tot_students})")

        if s.accessible_required and not room.accessible:
            violations.append(f"Session {sid} requires accessible room but room {room_id} is not accessible")

        # Maintenance check
        for m in room.maintenance_windows:
            if m.get("day") == day:
                m_start = PERIOD_INDEX.get(m.get("start_period"), -1)
                m_end = PERIOD_INDEX.get(m.get("end_period"), -1)
                for p in covered:
                    pi = PERIOD_INDEX.get(p, -1)
                    if m_start <= pi <= m_end:
                        violations.append(f"Room {room_id} under maintenance during {day} {p} (session {sid})")

        # Room overlap check
        for p in covered:
            k = (room_id, day, p)
            if k in room_occupancy:
                violations.append(f"Room conflict: Room {room_id} assigned to both {room_occupancy[k]} and {sid} at {day} {p}")
            else:
                room_occupancy[k] = sid

        # Faculty checks
        for fid in s.faculty_ids:
            fac = faculty_by_id.get(fid)
            if not fac:
                violations.append(f"Unknown faculty {fid} in session {sid}")
                continue

            for un in fac.unavailability:
                if un.get("day") == day and any(p in un.get("periods", []) for p in covered):
                    violations.append(f"Faculty {fid} is unavailable on {day} during {covered} (session {sid})")

            for p in covered:
                fk = (fid, day, p)
                if fk in faculty_occupancy:
                    violations.append(f"Faculty conflict: Faculty {fid} assigned to both {faculty_occupancy[fk]} and {sid} at {day} {p}")
                else:
                    faculty_occupancy[fk] = sid

            fdk = (fid, day)
            faculty_daily_hours[fdk] = faculty_daily_hours.get(fdk, 0) + dur

        # Student group checks
        basket = s.elective_basket
        for gid in s.student_groups:
            for p in covered:
                gk = (gid, day, p)
                if gk in group_occupancy:
                    clashing = group_occupancy[gk]
                    can_share = all(b is not None and b == basket for (_, b) in clashing)
                    if not can_share:
                        violations.append(f"Student group conflict: Group {gid} has multiple sessions at {day} {p}: {[x[0] for x in clashing]} and {sid}")
                    clashing.append((sid, basket))
                else:
                    group_occupancy[gk] = [(sid, basket)]

        # Basket sync
        if basket:
            if basket not in basket_slots:
                basket_slots[basket] = (day, start_period)
            else:
                ed, ep = basket_slots[basket]
                if day != ed or start_period != ep:
                    violations.append(f"Elective basket {basket} sessions out of sync: {sid} is at {day} {start_period}, expected {ed} {ep}")

    # Missing sessions check
    missing = set(sessions_by_id.keys()) - assigned_session_ids
    if missing:
        violations.append(f"Missing {len(missing)} sessions from schedule: {list(missing)[:5]}")

    # Faculty daily limits
    for (fid, day), total_h in faculty_daily_hours.items():
        limit = faculty_by_id[fid].daily_limit_hours
        if total_h > limit:
            violations.append(f"Faculty {fid} exceeded daily limit on {day}: {total_h} hours (limit {limit})")

    return {
        "is_valid": len(violations) == 0,
        "violations_count": len(violations),
        "violations": violations
    }
