# CIT Campus Scheduling & Venue Management — Starter Pack

Welcome to the official starter pack for the Chilika Institute of Technology (CIT) Timetable & Venue Management hackathon track.

## Contents
- `cit_public.json`: Complete benchmark dataset for Week 7 (Rooms, Faculty, Groups, Courses, Sessions, Bookings, Exams).
- `csv/`: Entity CSV spreadsheets (`rooms.csv`, `faculty.csv`, `student_groups.csv`, `courses.csv`, `sessions.csv`).
- `validator.py`: The official Python evaluation engine for hard constraints, soft penalties, booking scores, and moved-session metrics.
- `sample_disruption.json`: Sample disruption file specifying faculty leave, room closure, and a new makeup session.

---

## Dataset Schema

### 1. Rooms (`rooms`)
Total: 27 venues
- `id`: Unique identifier (e.g., `AUD`, `OAT`, `SH-1`, `LH-1`, `CR-1`, `LAB-CS1`, `LAB-PHY`)
- `name`: Human-readable name
- `type`: `auditorium`, `open_air_theatre`, `seminar_hall`, `lecture_hall`, `classroom`, `computer_lab`, `physics_lab`, `chemistry_lab`, `electrical_lab`, `mechanical_lab`, `civil_lab`
- `capacity`: Maximum seating capacity
- `accessible`: Boolean (`true` if ground floor / elevator-accessible)
- `features`: List of special amenities (`["projector", "ac", "sound_system", "stage", "computers", "lathes", ... ]`)
- `maintenance_windows`: Windows during which the room cannot be booked or used (`[{"day": "Wed", "start_period": "P8", "end_period": "P9"}]`)

### 2. Faculty (`faculty`)
Total: 40 instructors
- `id`: `F01` to `F40`
- `name`: Faculty name
- `department`: `CSE`, `ECE`, `ME`, `CE`, `EE`, `BS` (Basic Sciences)
- `daily_limit_hours`: Hard maximum teaching hours per day (4 hours for CIT)
- `unavailability`: Known unavailable periods (`[{"day": "Fri", "periods": ["P8", "P9"]}]`)
- `avoid_periods`: Soft preference periods to avoid (e.g., `["P1"]`, `["P9"]`)

### 3. Student Groups (`student_groups`)
Total: 14 cohorts (~1,000 students)
- `id`: `Y1-A`, `Y1-B`, `Y1-C`, `Y1-D` (Year 1 sections); `Y2-CSE`, `Y2-ECE`, `Y2-ME`, `Y2-CE`, `Y2-EE` (Year 2); `Y3-CSE`, `Y3-ECE`, `Y3-ME`, `Y3-CE`, `Y3-EE` (Year 3)
- `name`: Display name
- `year`: 1, 2, or 3
- `size`: Number of students in group (56 to 72)
- `accessible_required`: `true` if any student in this group requires step-free accessible venues

### 4. Courses (`courses`)
Total: 62 courses
- `code`: e.g. `CS101`, `MA101`, `EC201`, `CS305A`
- `name`: Course title
- `department`: Offering department
- `year`: 1, 2, or 3
- `credits`: Academic credits

### 5. Sessions (`sessions`)
Total: 189 sessions (summing to exactly 243 teaching hours a week)
- `id`: `S001` to `S189`
- `course_code`: References `courses.code`
- `session_type`: `lecture`, `tutorial`, or `lab`
- `duration_hours`: 1, 2, or 3 (3-hour labs only in P2-P4 or P6-P8)
- `required_room_type`: Matches room type
- `student_groups`: List of group IDs
- `faculty_ids`: List of assigned instructor IDs
- `accessible_required`: Boolean
- `elective_basket`: Basket ID if elective (sessions sharing basket run concurrently in identical slot)
- `fixed_slot`: `{"day": "Mon", "period": "P2"}` if fixed

### 6. Midsem Exams (`exams`)
Total: 41 examinations
- Scheduled during the exam week (week following Week 7)
- **Rule:** Room effective capacity is halved (`room.capacity // 2 >= students`)

### 7. Booking Requests (`booking_requests`)
Total: 25 requests for Spectra week
- Categories: `institute_event`, `guest_lecture`, `department_event`, `club_event`
- Includes English and Hinglish original text
- Request `BK25` is marked as cancelled

---

## Output Format (`schedule.json`)

Your application must generate `exports/schedule.json` conforming to this schema:

```json
{
  "metadata": {
    "generated_at": "2026-10-31T15:30:00Z",
    "dataset_version": "1.0.0",
    "solver_status": "OPTIMAL"
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
      "room_ids": ["LH-1", "LH-2"]
    }
  ],
  "bookings": [
    {
      "booking_id": "BK01",
      "decision": "approved",
      "assigned_room": "AUD",
      "day": "Wed",
      "start_period": "P6",
      "end_period": "P8",
      "reason": "Auditorium is available and satisfies capacity 350."
    }
  ]
}
```

---

## Validator Invocation

To evaluate any generated schedule:

```bash
python starter-pack/validator.py starter-pack/cit_public.json exports/schedule.json
```

For disruption rescheduling (evaluating moved sessions):

```bash
python starter-pack/validator.py starter-pack/cit_public.json exports/schedule_after.json exports/schedule.json
```

The script returns a JSON report with:
- `is_valid`: `true` if 0 hard violations
- `hard_violations_count`: number of hard violations
- `hard_violations`: detailed conflict list
- `soft_penalties`: breakdown of all soft costs
- `booking_score`: cumulative score for Spectra requests
- `moved_sessions_count`: number of sessions shifted during repair
