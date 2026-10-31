# CIT Campus Scheduling & Venue Management — Dataset & Architecture Notes

## 1. Starter Pack Review & Summary

We have thoroughly verified and documented the official Chilika Institute of Technology (CIT) dataset, constraints, and validation specifications.

### 1.1 Entities & Cardinality
| Entity | Count | Key Attributes |
|---|---|---|
| **Rooms** | **27** | `id`, `name`, `type`, `capacity`, `accessible`, `features`, `maintenance_windows` |
| **Faculty** | **40** | `id`, `name`, `department`, `daily_limit_hours` (4h), `unavailability`, `avoid_periods` |
| **Student Groups** | **14** | `id`, `name`, `year`, `size` (56-72), `accessible_required` |
| **Courses** | **62** | `code`, `name`, `department`, `year`, `credits` |
| **Sessions** | **189** | `id`, `course_code`, `session_type`, `duration_hours`, `required_room_type`, `student_groups`, `faculty_ids`, `accessible_required`, `elective_basket`, `fixed_slot` |
| **Midsem Exams** | **41** | `id`, `course_code`, `student_groups`, `student_count`, `duration_hours`, `preferred_room_types` |
| **Booking Requests** | **25** | `id`, `requester_name`, `category`, `day`, `start_period`, `end_period`, `preferred_room`, `expected_attendance`, English/Hinglish text (1 cancelled) |

**Total Teaching Hours:** Exactly **243 teaching hours** across the 189 sessions:
- 27 3-hour lab sessions (81 hours)
- 162 1-hour lectures & tutorials (162 hours)
- 81 + 162 = **243 teaching hours**

---

## 2. Hard & Soft Constraint Model

### Hard Constraints
1. **Uniqueness**: Every session is scheduled exactly once in a single room on one day.
2. **Faculty Conflict-Free**: No faculty member scheduled for overlapping periods.
3. **Student Group Conflict-Free**: No student group scheduled for overlapping periods, with the exception of sessions sharing an identical elective basket.
4. **Room Conflict-Free**: No room double-booked.
5. **Room Capacity**: `room.capacity >= sum(group.size)`. For exams: effective capacity is halved (`room.capacity // 2 >= students`).
6. **Room Type Consistency**: Labs run only in corresponding dedicated labs. Lecture halls and classrooms mapped appropriately.
7. **Accessibility**: Sessions/groups with `accessible_required=True` must receive ground-floor or elevator-accessible rooms (`accessible=True`).
8. **Lunch Break**: No session may cross the 13:00–14:00 lunch break (between P5 and P6).
9. **Lab Windows**: 3-hour labs only run in P2–P4 or P6–P8.
10. **Maintenance Windows**: Rooms undergoing maintenance cannot host sessions.
11. **Faculty Daily Limits**: Max 4 hours of teaching per instructor per day.
12. **Fixed Slots**: Pre-assigned day and period must be honored.
13. **Elective Basket Alignment**: All sessions in the same basket run at the exact same day and start period.
14. **Bookings & Priority**: Approved bookings cannot clash with classes, exams, or higher-priority bookings.

### Soft Constraints & Penalties
1. Faculty avoid preferences: penalty of 5 per period.
2. Student group schedule gaps (excluding lunch): penalty of 3 per gap period.
3. Student group daily load >6 hours: penalty of 10 per additional hour.
4. Duplicate lectures of the same course on the same day for a group: penalty of 8.
5. Room utilization below 40%: penalty of 4.
6. Period P9 (17:00–18:00) usage: penalty of 6.

---

## 3. Official Validator Invocation & Export Format

### Command Line
```bash
python starter-pack/validator.py starter-pack/cit_public.json exports/schedule.json [exports/schedule_base.json]
```

### Export Format (`exports/schedule.json`)
```json
{
  "metadata": {
    "generated_at": "ISO-8601 UTC timestamp",
    "dataset_version": "1.0.0",
    "solver_status": "OPTIMAL / FEASIBLE",
    "soft_penalty": 0
  },
  "timetable": [
    {
      "session_id": "S001",
      "day": "Mon",
      "start_period": "P2",
      "room_id": "LAB-CS1"
    }
  ],
  "exams": [
    {
      "exam_id": "EXAM01",
      "day": "Mon",
      "start_period": "P2",
      "room_ids": ["LH-1"]
    }
  ],
  "bookings": [
    {
      "booking_id": "BK01",
      "decision": "approved | rejected | alternative_offered",
      "assigned_room": "AUD",
      "day": "Wed",
      "start_period": "P6",
      "end_period": "P8",
      "reason": "Auditorium is available and satisfies capacity 350."
    }
  ]
}
```

This completes Step 1 of the build order.
