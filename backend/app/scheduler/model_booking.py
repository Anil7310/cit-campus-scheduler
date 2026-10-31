import logging
from typing import Dict, List, Any, Optional, Tuple
from app.scheduler.dataset_adapter import Dataset, BookingRequest, Room, PERIODS, PERIOD_INDEX
from app.scheduler.candidates import is_room_type_compatible

logger = logging.getLogger("cit_scheduler.model_booking")

PRIORITY_MAP = {
    "exam": 1,
    "regular_class": 2,
    "institute_event": 3,
    "guest_lecture": 4,
    "department_event": 5,
    "club_event": 6
}

class BookingDecisionEngine:
    def __init__(self, dataset: Dataset, timetable_assignments: List[Dict[str, Any]]):
        self.dataset = dataset
        self.timetable_assignments = timetable_assignments
        # Build class occupancy map: (room_id, day, period) -> session_id
        self.class_occupancy = {}
        for a in timetable_assignments:
            sid = a["session_id"]
            s = self.dataset.sessions_by_id.get(sid)
            dur = s.duration_hours if s else 1
            s_idx = PERIOD_INDEX.get(a["start_period"], 0)
            for i in range(dur):
                if s_idx + i < len(PERIODS):
                    p = PERIODS[s_idx + i]
                    self.class_occupancy[(a["room_id"], a["day"], p)] = sid

        # Map for approved bookings: (room_id, day, period) -> (booking_id, priority)
        self.booking_occupancy = {}

    def decide_all(self, requests: Optional[List[BookingRequest]] = None) -> List[Dict[str, Any]]:
        reqs = requests or self.dataset.booking_requests
        
        # Sort requests by priority (highest priority first), then by ID
        sorted_reqs = sorted(
            reqs,
            key=lambda r: (PRIORITY_MAP.get(r.category, 6), r.id)
        )

        decisions = []
        for req in sorted_reqs:
            dec = self.evaluate_request(req)
            decisions.append(dec)

        # Re-sort to match original request order
        original_order = {r.id: i for i, r in enumerate(reqs)}
        decisions.sort(key=lambda d: original_order.get(d["booking_id"], 999))
        return decisions

    def evaluate_request(self, req: BookingRequest) -> Dict[str, Any]:
        bid = req.id
        if req.status == "cancelled" or "cancelled" in (req.original_text or "").lower():
            return {
                "booking_id": bid,
                "title": req.title,
                "category": req.category,
                "decision": "rejected",
                "assigned_room": None,
                "day": req.day,
                "start_period": req.start_period,
                "end_period": req.end_period,
                "reason": "Request was formally cancelled by the requester.",
                "evidence": {"cancelled_by_requester": True}
            }

        s_idx = PERIOD_INDEX.get(req.start_period, 0)
        e_idx = PERIOD_INDEX.get(req.end_period, s_idx)
        covered_periods = [PERIODS[i] for i in range(s_idx, e_idx + 1) if i < len(PERIODS)]
        day = req.day
        req_prio = PRIORITY_MAP.get(req.category, 6)

        # Preferred room
        preferred_room = req.preferred_room
        target_rooms = []
        if preferred_room and preferred_room in self.dataset.rooms_by_id:
            target_rooms.append(self.dataset.rooms_by_id[preferred_room])
        
        # Add other candidate rooms matching type, capacity, and features
        for r in self.dataset.rooms:
            if r.id == preferred_room:
                continue
            if not is_room_type_compatible(req.required_room_type, r.type):
                continue
            if r.capacity < req.expected_attendance:
                continue
            if req.features_needed and not all(f in r.features for f in req.features_needed):
                continue
            target_rooms.append(r)

        # Check preferred room first
        primary_room = target_rooms[0] if target_rooms else None
        if primary_room:
            # Check capacity
            if primary_room.capacity < req.expected_attendance:
                return {
                    "booking_id": bid,
                    "title": req.title,
                    "category": req.category,
                    "decision": "rejected",
                    "assigned_room": None,
                    "day": day,
                    "start_period": req.start_period,
                    "end_period": req.end_period,
                    "reason": f"Preferred venue {primary_room.id} capacity ({primary_room.capacity}) is insufficient for expected attendance ({req.expected_attendance}).",
                    "evidence": {"room_capacity": primary_room.capacity, "attendance": req.expected_attendance}
                }

            # Check maintenance
            under_maint = False
            for m in primary_room.maintenance_windows:
                if m.get("day") == day:
                    m_s = PERIOD_INDEX.get(m.get("start_period"), -1)
                    m_e = PERIOD_INDEX.get(m.get("end_period"), -1)
                    if any(m_s <= PERIOD_INDEX.get(p, -1) <= m_e for p in covered_periods):
                        under_maint = True
                        break
            if under_maint:
                return {
                    "booking_id": bid,
                    "title": req.title,
                    "category": req.category,
                    "decision": "rejected",
                    "assigned_room": None,
                    "day": day,
                    "start_period": req.start_period,
                    "end_period": req.end_period,
                    "reason": f"Venue {primary_room.id} is undergoing scheduled maintenance during {day} {req.start_period}-{req.end_period}.",
                    "evidence": {"maintenance": True, "room_id": primary_room.id}
                }

            # Check clash with regular classes
            class_conflicts = []
            for p in covered_periods:
                k = (primary_room.id, day, p)
                if k in self.class_occupancy:
                    class_conflicts.append((p, self.class_occupancy[k]))

            # Check clash with prior approved bookings
            booking_conflicts = []
            for p in covered_periods:
                k = (primary_room.id, day, p)
                if k in self.booking_occupancy:
                    booking_conflicts.append((p, self.booking_occupancy[k]))

            if not class_conflicts and not booking_conflicts:
                # Approve!
                for p in covered_periods:
                    self.booking_occupancy[(primary_room.id, day, p)] = (bid, req_prio)

                return {
                    "booking_id": bid,
                    "title": req.title,
                    "category": req.category,
                    "decision": "approved",
                    "assigned_room": primary_room.id,
                    "day": day,
                    "start_period": req.start_period,
                    "end_period": req.end_period,
                    "reason": f"Approved in {primary_room.name} ({primary_room.id}). Venue is free and satisfies capacity {primary_room.capacity} for attendance {req.expected_attendance}.",
                    "evidence": {"room_id": primary_room.id, "capacity": primary_room.capacity, "clashes": []}
                }
            else:
                # Primary venue has conflict; search for an alternative
                alt_room = self._find_alternative_room(target_rooms[1:], day, covered_periods, req_prio)
                if alt_room:
                    for p in covered_periods:
                        self.booking_occupancy[(alt_room.id, day, p)] = (bid, req_prio)

                    conflict_desc = []
                    if class_conflicts:
                        conflict_desc.append(f"regular class {class_conflicts[0][1]}")
                    if booking_conflicts:
                        conflict_desc.append(f"booking {booking_conflicts[0][1][0]}")

                    return {
                        "booking_id": bid,
                        "title": req.title,
                        "category": req.category,
                        "decision": "alternative_offered",
                        "assigned_room": alt_room.id,
                        "day": day,
                        "start_period": req.start_period,
                        "end_period": req.end_period,
                        "alternative": {
                            "room_id": alt_room.id,
                            "day": day,
                            "start_period": req.start_period,
                            "end_period": req.end_period
                        },
                        "reason": f"Requested venue {primary_room.id} is occupied by {', '.join(conflict_desc)}. Alternative offered in {alt_room.name} ({alt_room.id}) at the same time.",
                        "evidence": {
                            "primary_conflicts": [f"{p}: {sid}" for p, sid in class_conflicts],
                            "alternative_room": alt_room.id
                        }
                    }
                else:
                    # Infeasible in any compatible room
                    evidence_items = [f"Class {sid} at {p}" for p, sid in class_conflicts] + [f"Booking {b[0]} at {p}" for p, b in booking_conflicts]
                    return {
                        "booking_id": bid,
                        "title": req.title,
                        "category": req.category,
                        "decision": "rejected",
                        "assigned_room": None,
                        "day": day,
                        "start_period": req.start_period,
                        "end_period": req.end_period,
                        "reason": f"Requested venue {primary_room.id} is occupied at {day} {req.start_period}-{req.end_period} by higher-priority event, and no compatible alternative venue is available.",
                        "evidence": {"conflicts": evidence_items}
                    }

        return {
            "booking_id": bid,
            "title": req.title,
            "category": req.category,
            "decision": "rejected",
            "assigned_room": None,
            "day": day,
            "start_period": req.start_period,
            "end_period": req.end_period,
            "reason": f"No available venue satisfies room type '{req.required_room_type}' and attendance {req.expected_attendance}.",
            "evidence": {"compatible_rooms_found": 0}
        }

    def _find_alternative_room(self, rooms: List[Room], day: str, covered_periods: List[str], req_prio: int) -> Optional[Room]:
        for r in rooms:
            clash = False
            for p in covered_periods:
                if (r.id, day, p) in self.class_occupancy or (r.id, day, p) in self.booking_occupancy:
                    clash = True
                    break
            if not clash:
                return r
        return None
