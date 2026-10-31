from typing import List, Dict, Tuple, Any
from app.scheduler.dataset_adapter import Dataset, Session, Room, Faculty, DAYS, TEACHING_PERIODS, PERIODS, PERIOD_INDEX

class Candidate:
    def __init__(self, session_id: str, day: str, start_period: str, room_id: str, covered_periods: List[str], soft_cost: int):
        self.session_id = session_id
        self.day = day
        self.start_period = start_period
        self.room_id = room_id
        self.covered_periods = covered_periods
        self.soft_cost = soft_cost

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "day": self.day,
            "start_period": self.start_period,
            "room_id": self.room_id,
            "covered_periods": self.covered_periods,
            "soft_cost": self.soft_cost
        }

def is_room_type_compatible(required_type: str, room_type: str) -> bool:
    if "lab" in required_type or required_type in ["open_air_theatre", "auditorium", "seminar_hall"]:
        return room_type == required_type
    if required_type == "classroom":
        return room_type in ["classroom", "lecture_hall"]
    if required_type == "lecture_hall":
        return room_type in ["lecture_hall", "auditorium"]
    return room_type == required_type

def generate_candidates_for_session(session: Session, dataset: Dataset, extra_disruptions: Any = None) -> List[Candidate]:
    candidates = []
    dur = session.duration_hours
    total_students = sum(dataset.groups_by_id[gid].size for gid in session.student_groups if gid in dataset.groups_by_id)

    # Filter rooms by static constraints: type, capacity, accessibility
    eligible_rooms = []
    for room in dataset.rooms:
        if not is_room_type_compatible(session.required_room_type, room.type):
            continue
        if room.capacity < total_students:
            continue
        if session.accessible_required and not room.accessible:
            continue
        eligible_rooms.append(room)

    # Days and periods to consider
    target_days = DAYS
    if session.fixed_slot and session.fixed_slot.get("day"):
        target_days = [session.fixed_slot["day"]]

    for day in target_days:
        for p_idx in range(len(TEACHING_PERIODS)):
            start_p = TEACHING_PERIODS[p_idx]
            if session.fixed_slot and session.fixed_slot.get("period") and session.fixed_slot["period"] != start_p:
                continue

            # Check if duration fits within teaching periods
            if p_idx + dur > len(TEACHING_PERIODS):
                continue

            covered = [TEACHING_PERIODS[p_idx + i] for i in range(dur)]

            # Lunch break constraint: P1-P5 is morning, P6-P9 is afternoon. No crossing lunch!
            crosses_lunch = any(p in ["P1", "P2", "P3", "P4", "P5"] for p in covered) and any(p in ["P6", "P7", "P8", "P9"] for p in covered)
            if crosses_lunch:
                continue

            # 3-hour lab constraint: only P2-P4 or P6-P8
            if session.session_type == "lab" and dur == 3:
                if covered != ["P2", "P3", "P4"] and covered != ["P6", "P7", "P8"]:
                    continue

            # Faculty availability
            fac_available = True
            soft_fac_avoid = 0
            for fid in session.faculty_ids:
                fac = dataset.faculty_by_id.get(fid)
                if not fac:
                    continue

                # Check static unavailability
                for un in fac.unavailability:
                    if un.get("day") == day and any(p in un.get("periods", []) for p in covered):
                        fac_available = False
                        break
                if not fac_available:
                    break

                # Soft avoid cost
                for p in covered:
                    if p in fac.avoid_periods:
                        soft_fac_avoid += 5

            if not fac_available:
                continue

            # Now test against eligible rooms
            for room in eligible_rooms:
                # Check room maintenance
                room_maint = False
                for m in room.maintenance_windows:
                    if m.get("day") == day:
                        m_start = PERIOD_INDEX.get(m.get("start_period"), -1)
                        m_end = PERIOD_INDEX.get(m.get("end_period"), -1)
                        for p in covered:
                            pi = PERIOD_INDEX.get(p, -1)
                            if m_start <= pi <= m_end:
                                room_maint = True
                                break
                    if room_maint:
                        break
                if room_maint:
                    continue

                # Compute soft cost
                candidate_soft_cost = soft_fac_avoid
                if "P9" in covered:
                    candidate_soft_cost += 6
                if room.capacity > 0 and (total_students / room.capacity) < 0.40:
                    candidate_soft_cost += 4

                candidates.append(Candidate(
                    session_id=session.id,
                    day=day,
                    start_period=start_p,
                    room_id=room.id,
                    covered_periods=covered,
                    soft_cost=candidate_soft_cost
                ))

    return candidates

def generate_all_candidates(dataset: Dataset) -> Dict[str, List[Candidate]]:
    candidates_by_session = {}
    for s in dataset.sessions:
        cands = generate_candidates_for_session(s, dataset)
        candidates_by_session[s.id] = cands
    return candidates_by_session
