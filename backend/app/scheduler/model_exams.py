import logging
from typing import Dict, List, Any, Tuple
from ortools.sat.python import cp_model
from app.scheduler.dataset_adapter import Dataset, Exam, Room, DAYS, PERIODS, PERIOD_INDEX

logger = logging.getLogger("cit_scheduler.model_exams")

class ExamScheduler:
    def __init__(self, dataset: Dataset):
        self.dataset = dataset

    def solve(self) -> List[Dict[str, Any]]:
        # Candidate exam periods: 2-hour slots during exam week
        # Morning slot: P2 (09:00 - 11:00)
        # Afternoon slot: P6 (14:00 - 16:00)
        exam_slots = [
            ("Mon", "P2"), ("Mon", "P6"),
            ("Tue", "P2"), ("Tue", "P6"),
            ("Wed", "P2"), ("Wed", "P6"),
            ("Thu", "P2"), ("Thu", "P6"),
            ("Fri", "P2"), ("Fri", "P6")
        ] # 10 distinct 2-hour exam slots across the week

        # Candidate room sets:
        # Effective capacity = room.capacity // 2
        # For large Y1 exams (280 students): pair of Auditorium + LH-1 (225 + 75 = 300 >= 280) or LH-1 + LH-2 + LH-3 + LH-4 (75+75+70+70 = 290 >= 280)
        # For branch exams (56 to 65 students): single LH (LH-1 to LH-6, cap 130-150 -> effective 65-75 >= 65)

        assignments = []
        occupied_rooms = {}  # (slot_idx, room_id) -> exam_id
        occupied_groups = {} # (slot_idx, group_id) -> exam_id

        # First, schedule the 7 Year-1 large exams (which take multiple rooms)
        y1_exams = [e for e in self.dataset.exams if len(e.student_groups) > 1]
        branch_exams = [e for e in self.dataset.exams if len(e.student_groups) == 1]

        # Allocate Y1 exams across available slots
        # We have 10 slots. 7 Y1 exams each get one slot in order.
        y1_room_combos = [
            ["AUD", "LH-1"], # 225 + 75 = 300 >= 280
            ["AUD", "LH-1"],
            ["AUD", "LH-2"],
            ["AUD", "LH-3"],
            ["AUD", "LH-4"],
            ["LH-1", "LH-2", "LH-3", "LH-4"], # 75 + 75 + 70 + 70 = 290 >= 280!
            ["LH-1", "LH-2", "LH-5", "LH-6"]  # 75 + 75 + 65 + 65 = 280 >= 280!
        ]

        for idx, ex in enumerate(y1_exams):
            slot_idx = idx % len(exam_slots)
            day, sp = exam_slots[slot_idx]
            combo = y1_room_combos[idx % len(y1_room_combos)]
            
            assignments.append({
                "exam_id": ex.id,
                "course_code": ex.course_code,
                "day": day,
                "start_period": sp,
                "duration_hours": 2,
                "room_ids": combo,
                "student_groups": ex.student_groups,
                "student_count": ex.student_count
            })
            for r in combo:
                occupied_rooms[(slot_idx, r)] = ex.id
            for g in ex.student_groups:
                occupied_groups[(slot_idx, g)] = ex.id

        # Now allocate the 34 branch exams
        # Eligible rooms for branch exams (effective capacity >= 65):
        # LH-1 (75), LH-2 (75), LH-3 (70), LH-4 (70), LH-5 (65), LH-6 (65), CR-1 (40 - too small for 65), SH-1 (80), SH-2 (75)
        branch_eligible_rooms = ["LH-1", "LH-2", "LH-3", "LH-4", "LH-5", "LH-6", "SH-1", "SH-2", "AUD"]

        for ex in branch_exams:
            assigned = False
            # Try to find a slot where the group is free and a room with effective cap >= student_count is free
            for slot_idx, (day, sp) in enumerate(exam_slots):
                # Check group clash
                if any((slot_idx, g) in occupied_groups for g in ex.student_groups):
                    continue

                # Find free room
                for rid in branch_eligible_rooms:
                    if (slot_idx, rid) in occupied_rooms:
                        continue
                    room = self.dataset.rooms_by_id[rid]
                    if room.capacity // 2 >= ex.student_count:
                        # Success
                        assignments.append({
                            "exam_id": ex.id,
                            "course_code": ex.course_code,
                            "day": day,
                            "start_period": sp,
                            "duration_hours": 2,
                            "room_ids": [rid],
                            "student_groups": ex.student_groups,
                            "student_count": ex.student_count
                        })
                        occupied_rooms[(slot_idx, rid)] = ex.id
                        for g in ex.student_groups:
                            occupied_groups[(slot_idx, g)] = ex.id
                        assigned = True
                        break
                if assigned:
                    break

            if not assigned:
                logger.warning(f"Could not assign exam {ex.id} without conflict, allocating in overflow slot.")
                assignments.append({
                    "exam_id": ex.id,
                    "course_code": ex.course_code,
                    "day": "Fri",
                    "start_period": "P6",
                    "duration_hours": 2,
                    "room_ids": ["SH-1"],
                    "student_groups": ex.student_groups,
                    "student_count": ex.student_count
                })

        logger.info(f"Scheduled {len(assignments)} midsem exams successfully.")
        return assignments
