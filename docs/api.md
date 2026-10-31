# CIT Platform REST API Documentation

Base URL: `/api/v1`

All authenticated endpoints require an `Authorization: Bearer <JWT_TOKEN>` header.

---

## 1. Authentication (`/auth`)

### `POST /auth/login`
- **Request Body:** `{ "email": "admin@cit.edu", "password": "..." }`
- **Response:** `{ "access_token": "...", "token_type": "bearer", "user": { ... } }`

### `GET /auth/me`
- **Response:** Current authenticated user profile with role and department.

---

## 2. Timetable Management (`/timetable`)

### `GET /timetable/schedule`
- **Response:** Full baseline timetable (189 sessions) matching `exports/schedule.json`.

### `GET /timetable/schedule-after`
- **Response:** Post-disruption schedule matching `exports/schedule_after.json` including the list of 4 moved sessions.

### `GET /timetable/sessions`
- **Query Parameters:** `group_id`, `faculty_id`, `room_id`.
- **Response:** Filtered session list.

### `GET /timetable/explain?session_id=S001`
- **Response:** Decision breakdown for session $s$, list of hard constraints satisfied, and count of alternative slots evaluated.

---

## 3. Real-Time Room Vacancy (`/views`)

### `GET /views/free-rooms`
- **Query Parameters:** `day` (`MON`..`FRI`), `start_period` (1..9), `duration` (1..3), `min_capacity`, `room_type`.
- **Response:** `{ "available_rooms": [...], "total_checked": 27 }`

---

## 4. Midsem Exams (`/exams`)

### `GET /exams`
- **Response:** All 41 midsem exams with student group breakdown, assigned venues, and verified halved room seating capacity.

---

## 5. Venue Bookings (`/bookings`)

### `GET /bookings`
- **Response:** List of all active booking requests and their status.

### `POST /bookings`
- **Request Body:** `{ "title": "...", "category": "CLUB", "requested_room": "LH-1", "day": "THU", "start_period": 6, "duration": 2 }`
- **Response:** Evaluated booking request.

### `POST /bookings/{id}/approve`
- **Guards:** Requires `admin` or `coordinator` role. Prevents self-approval.
- **Response:** Approved booking request.

### `POST /bookings/{id}/reject`
- **Request Body:** `{ "reason": "..." }`
- **Response:** Rejected booking request with recorded reason.

### `POST /bookings/run-spectra`
- **Role:** Administrator / Coordinator.
- **Response:** Re-executes the Spectra 25-request priority optimization engine.

---

## 6. Rescheduling & Disruptions (`/rescheduling`)

### `GET /rescheduling/disruptions`
- **Response:** Current active disruption events.

### `POST /rescheduling/apply-sample`
- **Response:** Triggers Gate C benchmark disruptions (`sample_disruption.json`) and returns exact diffs and moved count.

---

## 7. AI Conversational Assistant (`/assistant`)

### `POST /assistant/chat`
- **Request Body:** `{ "message": "Kal subah 10 baje CR-1 khali hai kya?" }`
- **Response:** `{ "action": "QUERY", "feasible": true, "explanation": "...", "recommended_slot": { ... } }`

---

## 8. Manual Overrides (`/manual`)

### `POST /manual/validate-move`
- **Request Body:** `{ "session_id": "S001", "new_day": "MON", "new_start_period": 2, "new_room_id": "CR-2" }`
- **Response:** `{ "is_valid": true|false, "hard_violations": [...], "soft_penalty_delta": 10 }`

### `POST /manual/commit-move`
- **Request Body:** `{ "session_id": "...", "new_day": "...", "new_start_period": ..., "new_room_id": "..." }`
- **Response:** Updates master schedule and records an immutable audit log.

---

## 9. Governance & Maintenance (`/admin`)

### `POST /admin/reset-demo`
- **Role:** System Administrator.
- **Response:** Restores all collections to pristine benchmark state.

### `GET /admin/audit-logs`
- **Response:** Tamper-resistant log entries of all administrative interventions.
