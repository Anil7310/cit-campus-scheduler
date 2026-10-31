import logging
import copy
from typing import Dict, List, Any, Tuple, Optional
from ortools.sat.python import cp_model
from app.scheduler.dataset_adapter import Dataset, Session, Room, Faculty, DAYS, TEACHING_PERIODS, PERIOD_INDEX, PERIODS
from app.scheduler.candidates import generate_candidates_for_session, Candidate

logger = logging.getLogger("cit_scheduler.repair")

class ReschedulingEngine:
    def __init__(self, dataset: Dataset, base_assignments: List[Dict[str, Any]]):
        self.dataset = copy.deepcopy(dataset)
        self.base_assignments = base_assignments
        self.base_map = {a["session_id"]: a for a in base_assignments}

    def apply_disruptions(self, disruptions: List[Dict[str, Any]], time_limit_seconds: int = 30) -> Dict[str, Any]:
        """
        Solves the repair problem with lexicographic objective:
        (1) Minimise number of moved sessions
        (2) Minimise soft penalty
        """
        # Apply disruptions to the dataset representation
        faculty_leaves = [] # (fid, day, set_of_periods)
        room_closures = []  # (rid, day, set_of_periods)
        new_sessions = []

        for d in disruptions:
            dtype = d.get("type")
            if dtype == "faculty_leave":
                fid = d.get("faculty_id")
                day = d.get("day")
                s_i = PERIOD_INDEX.get(d.get("start_period"), 0)
                e_i = PERIOD_INDEX.get(d.get("end_period"), s_i)
                periods = set(PERIODS[i] for i in range(s_i, e_i + 1) if i < len(PERIODS))
                faculty_leaves.append((fid, day, periods))

            elif dtype == "room_closure":
                rid = d.get("room_id")
                day = d.get("day")
                s_i = PERIOD_INDEX.get(d.get("start_period"), 0)
                e_i = PERIOD_INDEX.get(d.get("end_period"), s_i)
                periods = set(PERIODS[i] for i in range(s_i, e_i + 1) if i < len(PERIODS))
                room_closures.append((rid, day, periods))

            elif dtype == "new_session":
                s_dict = d.get("session", {})
                new_s = Session(
                    id=s_dict.get("id", f"S_NEW_{len(new_sessions)+1}"),
                    course_code=s_dict.get("course_code", "GEN101"),
                    session_type=s_dict.get("session_type", "lecture"),
                    duration_hours=s_dict.get("duration_hours", 1),
                    required_room_type=s_dict.get("required_room_type", "classroom"),
                    student_groups=s_dict.get("student_groups", []),
                    faculty_ids=s_dict.get("faculty_ids", []),
                    accessible_required=s_dict.get("accessible_required", False)
                )
                new_sessions.append(new_s)

        # Build combined list of sessions
        all_sessions = list(self.dataset.sessions) + new_sessions
        sessions_by_id = {s.id: s for s in all_sessions}

        # Filter candidates accounting for disruptions
        candidates_by_session: Dict[str, List[Candidate]] = {}
        for s in all_sessions:
            cands = generate_candidates_for_session(s, self.dataset)
            valid_cands = []
            for c in cands:
                # Check faculty leave
                f_conflict = False
                for fid, l_day, l_periods in faculty_leaves:
                    if fid in s.faculty_ids and c.day == l_day and any(p in l_periods for p in c.covered_periods):
                        f_conflict = True
                        break
                if f_conflict:
                    continue

                # Check room closure
                r_conflict = False
                for rid, rc_day, rc_periods in room_closures:
                    if c.room_id == rid and c.day == rc_day and any(p in rc_periods for p in c.covered_periods):
                        r_conflict = True
                        break
                if r_conflict:
                    continue

                valid_cands.append(c)

            candidates_by_session[s.id] = valid_cands

        # Check for empty candidates
        infeasible_sessions = [s.id for s in all_sessions if not candidates_by_session[s.id]]
        if infeasible_sessions:
            return {
                "status": "INFEASIBLE",
                "message": f"Sessions {infeasible_sessions} have no valid slots under the disruption constraints.",
                "conflicts": infeasible_sessions,
                "diff": [],
                "moved_count": 0,
                "schedule": []
            }

        # Build CP-SAT Model
        model = cp_model.CpModel()
        x = {}
        moved = {}

        for s in all_sessions:
            cands = candidates_by_session[s.id]
            for c_idx, c in enumerate(cands):
                x[s.id, c_idx] = model.NewBoolVar(f"x_{s.id}_{c_idx}")

            # Exactly one candidate
            model.Add(sum(x[s.id, c_idx] for c_idx in range(len(cands))) == 1)

            # Move indicator for existing sessions
            if s.id in self.base_map:
                base_info = self.base_map[s.id]
                base_c_idx = None
                for c_idx, c in enumerate(cands):
                    if c.day == base_info["day"] and c.start_period == base_info["start_period"] and c.room_id == base_info["room_id"]:
                        base_c_idx = c_idx
                        break

                moved[s.id] = model.NewBoolVar(f"moved_{s.id}")
                if base_c_idx is not None:
                    # If base candidate is chosen, moved[s.id] == 0, else 1
                    model.Add(x[s.id, base_c_idx] + moved[s.id] == 1)
                else:
                    # Base candidate was invalidated by disruption
                    model.Add(moved[s.id] == 1)

        # Room non-overlapping
        room_occupancy = {}
        for s in all_sessions:
            for c_idx, c in enumerate(candidates_by_session[s.id]):
                for p in c.covered_periods:
                    k = (c.room_id, c.day, p)
                    if k not in room_occupancy:
                        room_occupancy[k] = []
                    room_occupancy[k].append(x[s.id, c_idx])
        for k, var_list in room_occupancy.items():
            if len(var_list) > 1:
                model.Add(sum(var_list) <= 1)

        # Faculty non-overlapping
        fac_occupancy = {}
        for s in all_sessions:
            for fid in s.faculty_ids:
                for c_idx, c in enumerate(candidates_by_session[s.id]):
                    for p in c.covered_periods:
                        k = (fid, c.day, p)
                        if k not in fac_occupancy:
                            fac_occupancy[k] = []
                        fac_occupancy[k].append(x[s.id, c_idx])
        for k, var_list in fac_occupancy.items():
            if len(var_list) > 1:
                model.Add(sum(var_list) <= 1)

        # Elective basket synchronization
        baskets: Dict[str, List[str]] = {}
        for s in all_sessions:
            if s.elective_basket:
                if s.elective_basket not in baskets:
                    baskets[s.elective_basket] = []
                baskets[s.elective_basket].append(s.id)

        basket_time_vars = {}
        for b_id, s_ids in baskets.items():
            time_slots = [(d, p) for d in DAYS for p in TEACHING_PERIODS]
            slot_vars = []
            for d, p in time_slots:
                b_var = model.NewBoolVar(f"rep_basket_{b_id}_{d}_{p}")
                basket_time_vars[b_id, d, p] = b_var
                slot_vars.append(b_var)
            model.Add(sum(slot_vars) == 1)

            for sid in s_ids:
                cands = candidates_by_session[sid]
                for d, p in time_slots:
                    matching_c_indices = [c_idx for c_idx, c in enumerate(cands) if c.day == d and c.start_period == p]
                    if matching_c_indices:
                        model.Add(sum(x[sid, c_idx] for c_idx in matching_c_indices) == basket_time_vars[b_id, d, p])
                    else:
                        model.Add(basket_time_vars[b_id, d, p] == 0)

        # Group non-overlapping
        group_occupancy = {}
        for s in all_sessions:
            for gid in s.student_groups:
                for c_idx, c in enumerate(candidates_by_session[s.id]):
                    for p in c.covered_periods:
                        k = (gid, c.day, p)
                        if k not in group_occupancy:
                            group_occupancy[k] = {}
                        b_key = s.elective_basket or f"single_{s.id}"
                        if b_key not in group_occupancy[k]:
                            group_occupancy[k][b_key] = []
                        group_occupancy[k][b_key].append(x[s.id, c_idx])

        for (gid, day, p), basket_dict in group_occupancy.items():
            occ_vars = []
            for b_key, var_list in basket_dict.items():
                if b_key.startswith("single_"):
                    occ_vars.extend(var_list)
                else:
                    b_occ = model.NewBoolVar(f"rep_grp_b_{gid}_{day}_{p}_{b_key}")
                    model.Add(sum(var_list) >= b_occ)
                    model.Add(sum(var_list) <= len(var_list) * b_occ)
                    occ_vars.append(b_occ)
            if len(occ_vars) > 1:
                model.Add(sum(occ_vars) <= 1)

        # Faculty daily limits
        for fac in self.dataset.faculty:
            for day in DAYS:
                d_terms = []
                for s in all_sessions:
                    if fac.id in s.faculty_ids:
                        for c_idx, c in enumerate(candidates_by_session[s.id]):
                            if c.day == day:
                                d_terms.append(x[s.id, c_idx] * s.duration_hours)
                if d_terms:
                    model.Add(sum(d_terms) <= fac.daily_limit_hours)

        # Objective: Minimise 10000 * moves + soft_costs
        obj_terms = [moved[sid] * 10000 for sid in moved]
        for s in all_sessions:
            for c_idx, c in enumerate(candidates_by_session[s.id]):
                if c.soft_cost > 0:
                    obj_terms.append(x[s.id, c_idx] * c.soft_cost)

        model.Minimize(sum(obj_terms))

        # Add solution hints from base schedule
        for sid, b_info in self.base_map.items():
            if sid in candidates_by_session:
                for c_idx, c in enumerate(candidates_by_session[sid]):
                    if c.day == b_info["day"] and c.start_period == b_info["start_period"] and c.room_id == b_info["room_id"]:
                        model.AddHint(x[sid, c_idx], 1)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(time_limit_seconds)
        solver.parameters.num_search_workers = 2
        solver.parameters.random_seed = 1

        status_code = solver.Solve(model)
        status_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.UNKNOWN: "UNKNOWN"
        }
        res_status = status_map.get(status_code, "UNKNOWN")

        if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            repaired_schedule = []
            diff = []
            moved_count = 0

            for s in all_sessions:
                chosen = None
                for c_idx, c in enumerate(candidates_by_session[s.id]):
                    if solver.Value(x[s.id, c_idx]) == 1:
                        chosen = c
                        break

                if chosen:
                    new_item = {
                        "session_id": s.id,
                        "day": chosen.day,
                        "start_period": chosen.start_period,
                        "room_id": chosen.room_id
                    }
                    repaired_schedule.append(new_item)

                    if s.id in self.base_map:
                        old_item = self.base_map[s.id]
                        if (old_item["day"] != chosen.day or 
                            old_item["start_period"] != chosen.start_period or 
                            old_item["room_id"] != chosen.room_id):
                            moved_count += 1
                            diff.append({
                                "session_id": s.id,
                                "course_code": s.course_code,
                                "old": {
                                    "day": old_item["day"],
                                    "period": old_item["start_period"],
                                    "room_id": old_item["room_id"]
                                },
                                "new": {
                                    "day": chosen.day,
                                    "period": chosen.start_period,
                                    "room_id": chosen.room_id
                                },
                                "reason": self._derive_move_reason(s, old_item, disruptions)
                            })
                    else:
                        # Newly added session
                        diff.append({
                            "session_id": s.id,
                            "course_code": s.course_code,
                            "old": None,
                            "new": {
                                "day": chosen.day,
                                "period": chosen.start_period,
                                "room_id": chosen.room_id
                            },
                            "reason": "Newly introduced makeup / guest session."
                        })

            return {
                "status": res_status,
                "moved_count": moved_count,
                "diff": diff,
                "schedule": repaired_schedule,
                "message": f"Successfully repaired timetable with {moved_count} moved sessions."
            }
        else:
            return {
                "status": res_status,
                "moved_count": 0,
                "diff": [],
                "schedule": [],
                "message": f"Rescheduling solver finished with status: {res_status}"
            }

    def _derive_move_reason(self, session: Session, old_item: Dict[str, Any], disruptions: List[Dict[str, Any]]) -> str:
        # Check why it moved
        for d in disruptions:
            if d.get("type") == "faculty_leave":
                if d.get("faculty_id") in session.faculty_ids and d.get("day") == old_item["day"]:
                    return f"Moved due to faculty leave for {d.get('faculty_id')} on {old_item['day']}."
            elif d.get("type") == "room_closure":
                if d.get("room_id") == old_item["room_id"] and d.get("day") == old_item["day"]:
                    return f"Moved due to temporary closure of venue {old_item['room_id']} on {old_item['day']}."
        return "Shifted to accommodate schedule constraint resolution with minimal overall moves."
