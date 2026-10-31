import logging
from typing import Dict, List, Tuple, Any, Optional
from ortools.sat.python import cp_model
from app.scheduler.dataset_adapter import Dataset, DAYS, TEACHING_PERIODS, PERIOD_INDEX
from app.scheduler.candidates import generate_all_candidates, Candidate

logger = logging.getLogger("cit_scheduler.model_timetable")

class TimetableSolver:
    def __init__(self, dataset: Dataset, time_limit_seconds: int = 60, num_workers: int = 2):
        self.dataset = dataset
        self.time_limit_seconds = time_limit_seconds
        self.num_workers = num_workers
        self.candidates_by_session = generate_all_candidates(dataset)

    def solve(self, base_hints: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        model = cp_model.CpModel()

        # Check for any session with 0 candidates
        for s in self.dataset.sessions:
            cands = self.candidates_by_session.get(s.id, [])
            if not cands:
                logger.error(f"Session {s.id} has 0 legal candidates! Model is infeasible.")
                return "INFEASIBLE", [], {"error": f"Session {s.id} has no valid candidates."}

        # 1. Variables: x[session_id, candidate_index]
        x = {}
        for s in self.dataset.sessions:
            cands = self.candidates_by_session[s.id]
            for c_idx, c in enumerate(cands):
                x[s.id, c_idx] = model.NewBoolVar(f"x_{s.id}_{c_idx}")

        # 2. Hard constraint: Exactly one candidate per session
        for s in self.dataset.sessions:
            cands = self.candidates_by_session[s.id]
            model.Add(sum(x[s.id, c_idx] for c_idx in range(len(cands))) == 1)

        # 3. Hard constraint: Room non-overlapping
        # For each room, day, period: sum <= 1
        room_day_period_cands = {}
        for s in self.dataset.sessions:
            for c_idx, c in enumerate(self.candidates_by_session[s.id]):
                for p in c.covered_periods:
                    key = (c.room_id, c.day, p)
                    if key not in room_day_period_cands:
                        room_day_period_cands[key] = []
                    room_day_period_cands[key].append(x[s.id, c_idx])

        for key, var_list in room_day_period_cands.items():
            if len(var_list) > 1:
                model.Add(sum(var_list) <= 1)

        # 4. Hard constraint: Faculty non-overlapping
        fac_day_period_cands = {}
        for s in self.dataset.sessions:
            for fid in s.faculty_ids:
                for c_idx, c in enumerate(self.candidates_by_session[s.id]):
                    for p in c.covered_periods:
                        key = (fid, c.day, p)
                        if key not in fac_day_period_cands:
                            fac_day_period_cands[key] = []
                        fac_day_period_cands[key].append(x[s.id, c_idx])

        for key, var_list in fac_day_period_cands.items():
            if len(var_list) > 1:
                model.Add(sum(var_list) <= 1)

        # 5. Hard constraint: Faculty daily teaching hour limit (4h)
        for fac in self.dataset.faculty:
            limit = fac.daily_limit_hours
            for day in DAYS:
                day_terms = []
                for s in self.dataset.sessions:
                    if fac.id in s.faculty_ids:
                        for c_idx, c in enumerate(self.candidates_by_session[s.id]):
                            if c.day == day:
                                day_terms.append(x[s.id, c_idx] * s.duration_hours)
                if day_terms:
                    model.Add(sum(day_terms) <= limit)

        # 6. Elective Baskets:
        # Group sessions by basket
        baskets: Dict[str, List[str]] = {}
        for s in self.dataset.sessions:
            if s.elective_basket:
                if s.elective_basket not in baskets:
                    baskets[s.elective_basket] = []
                baskets[s.elective_basket].append(s.id)

        basket_time_vars = {}
        for b_id, s_ids in baskets.items():
            # Possible (day, start_p)
            time_slots = [(d, p) for d in DAYS for p in TEACHING_PERIODS]
            slot_vars = []
            for d, p in time_slots:
                b_var = model.NewBoolVar(f"basket_{b_id}_{d}_{p}")
                basket_time_vars[b_id, d, p] = b_var
                slot_vars.append(b_var)
            model.Add(sum(slot_vars) == 1)

            # Link each session in basket to the basket variable
            for sid in s_ids:
                cands = self.candidates_by_session[sid]
                for d, p in time_slots:
                    matching_c_indices = [c_idx for c_idx, c in enumerate(cands) if c.day == d and c.start_period == p]
                    if matching_c_indices:
                        model.Add(sum(x[sid, c_idx] for c_idx in matching_c_indices) == basket_time_vars[b_id, d, p])
                    else:
                        model.Add(basket_time_vars[b_id, d, p] == 0)

        # 7. Student Group Non-overlapping (excluding shared basket sessions)
        group_day_period_terms = {}
        for s in self.dataset.sessions:
            for gid in s.student_groups:
                for c_idx, c in enumerate(self.candidates_by_session[s.id]):
                    for p in c.covered_periods:
                        key = (gid, c.day, p)
                        if key not in group_day_period_terms:
                            group_day_period_terms[key] = {}
                        
                        b_key = s.elective_basket or f"single_{s.id}"
                        if b_key not in group_day_period_terms[key]:
                            group_day_period_terms[key][b_key] = []
                        group_day_period_terms[key][b_key].append(x[s.id, c_idx])

        for (gid, day, p), basket_dict in group_day_period_terms.items():
            # For each distinct basket (or single session), create an occupancy boolean
            occ_vars = []
            for b_key, var_list in basket_dict.items():
                if b_key.startswith("single_"):
                    occ_vars.extend(var_list)
                else:
                    # For a basket slot, its occupancy is at most 1
                    b_occ = model.NewBoolVar(f"grp_b_occ_{gid}_{day}_{p}_{b_key}")
                    model.Add(sum(var_list) >= b_occ)
                    model.Add(sum(var_list) <= len(var_list) * b_occ)
                    occ_vars.append(b_occ)
            if len(occ_vars) > 1:
                model.Add(sum(occ_vars) <= 1)

        # 8. Soft Objective:
        # Sum of candidate soft costs + penalties
        cost_terms = []
        for s in self.dataset.sessions:
            for c_idx, c in enumerate(self.candidates_by_session[s.id]):
                if c.soft_cost > 0:
                    cost_terms.append(x[s.id, c_idx] * c.soft_cost)

        model.Minimize(sum(cost_terms))

        # Add solution hints if base schedule is provided
        if base_hints:
            for hint in base_hints:
                sid = hint.get("session_id")
                h_day = hint.get("day")
                h_sp = hint.get("start_period")
                h_room = hint.get("room_id")
                if sid in self.candidates_by_session:
                    for c_idx, c in enumerate(self.candidates_by_session[sid]):
                        if c.day == h_day and c.start_period == h_sp and c.room_id == h_room:
                            model.AddHint(x[sid, c_idx], 1)

        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self.time_limit_seconds)
        solver.parameters.num_search_workers = int(self.num_workers)
        solver.parameters.random_seed = 1

        logger.info(f"Solving timetable with CP-SAT (time_limit={self.time_limit_seconds}s, workers={self.num_workers})...")
        status_code = solver.Solve(model)

        status_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "MODEL_INVALID",
            cp_model.UNKNOWN: "UNKNOWN"
        }
        status_str = status_map.get(status_code, "UNKNOWN")
        logger.info(f"CP-SAT solver finished with status: {status_str}")

        if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            assignments = []
            for s in self.dataset.sessions:
                chosen_c = None
                for c_idx, c in enumerate(self.candidates_by_session[s.id]):
                    if solver.Value(x[s.id, c_idx]) == 1:
                        chosen_c = c
                        break
                if chosen_c:
                    assignments.append({
                        "session_id": s.id,
                        "day": chosen_c.day,
                        "start_period": chosen_c.start_period,
                        "room_id": chosen_c.room_id
                    })
                else:
                    logger.error(f"Session {s.id} was not assigned a candidate!")

            metrics = {
                "objective_value": solver.ObjectiveValue(),
                "wall_time": solver.WallTime(),
                "branches": solver.NumBranches()
            }
            return status_str, assignments, metrics
        else:
            return status_str, [], {"wall_time": solver.WallTime()}
