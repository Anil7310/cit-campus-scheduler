import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from app.ai.safety import sanitize_user_input

# Days mapping
DAYS_LEXICON = {
    "monday": "Mon", "somwar": "Mon", "mon": "Mon",
    "tuesday": "Tue", "mangalwar": "Tue", "tue": "Tue",
    "wednesday": "Wed", "budhwar": "Wed", "wed": "Wed",
    "thursday": "Thu", "guruwar": "Thu", "veervar": "Thu", "thu": "Thu",
    "friday": "Fri", "shukrawar": "Fri", "fri": "Fri",
    "aaj": "TODAY", "today": "TODAY",
    "kal": "TOMORROW", "tomorrow": "TOMORROW",
    "parso": "DAY_AFTER_TOMORROW"
}

# Room keywords mapping
ROOMS_LEXICON = {
    "auditorium": "AUD", "audi": "AUD", "main auditorium": "AUD",
    "open air theatre": "OAT", "oat": "OAT", "open air": "OAT",
    "seminar hall 1": "SH-1", "sh1": "SH-1", "sh-1": "SH-1",
    "seminar hall 2": "SH-2", "sh2": "SH-2", "sh-2": "SH-2", "seminar hall": "SH-1",
    "lecture hall 1": "LH-1", "lh1": "LH-1", "lh-1": "LH-1",
    "lecture hall 2": "LH-2", "lh2": "LH-2", "lh-2": "LH-2",
    "lecture hall 3": "LH-3", "lh3": "LH-3",
    "lecture hall": "LH-1", "lh": "LH-1",
    "computing lab 1": "LAB-CS1", "cs lab 1": "LAB-CS1", "lab cs1": "LAB-CS1",
    "computing lab 2": "LAB-CS2", "cs lab 2": "LAB-CS2", "computer lab": "LAB-CS1", "comp lab": "LAB-CS1",
    "physics lab": "LAB-PHY", "phy lab": "LAB-PHY",
    "chemistry lab": "LAB-CHE", "chem lab": "LAB-CHE",
    "electrical lab": "LAB-EE", "ee lab": "LAB-EE",
    "mechanical workshop": "LAB-ME", "mech lab": "LAB-ME", "workshop": "LAB-ME",
    "civil lab": "LAB-CE", "cr-1": "CR-1", "cr1": "CR-1", "cr-2": "CR-2", "cr2": "CR-2", "cr-3": "CR-3"
}

def parse_booking_intent_fallback(text: str) -> Dict[str, Any]:
    cleaned = sanitize_user_input(text).lower()
    missing_fields = []
    clarifying_question = None

    # 1. Day resolution
    detected_day = None
    for kw, d_val in DAYS_LEXICON.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
            if d_val == "TODAY":
                detected_day = "Mon" # Fixed academic baseline
            elif d_val == "TOMORROW":
                detected_day = "Tue"
            elif d_val == "DAY_AFTER_TOMORROW":
                detected_day = "Wed"
            else:
                detected_day = d_val
            break

    if not detected_day:
        detected_day = "Wed" # Default to Spectra peak day
        missing_fields.append("day")

    # 2. Room detection
    detected_room = None
    required_room_type = "classroom"
    for kw, rid in ROOMS_LEXICON.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
            detected_room = rid
            if "AUD" in rid:
                required_room_type = "auditorium"
            elif "OAT" in rid:
                required_room_type = "open_air_theatre"
            elif "SH" in rid:
                required_room_type = "seminar_hall"
            elif "LH" in rid:
                required_room_type = "lecture_hall"
            elif "LAB-CS" in rid:
                required_room_type = "computer_lab"
            elif "LAB-PHY" in rid:
                required_room_type = "physics_lab"
            elif "LAB-CHE" in rid:
                required_room_type = "chemistry_lab"
            elif "LAB-EE" in rid:
                required_room_type = "electrical_lab"
            elif "LAB-ME" in rid:
                required_room_type = "mechanical_lab"
            elif "LAB-CE" in rid:
                required_room_type = "civil_lab"
            break

    # 3. Time / Period detection
    start_p = "P6"
    end_p = "P7"

    # Explicit period patterns e.g. "p2-p4", "p10 to p12", "p3"
    period_match = re.search(r'\b(p[1-9]|p1[0-3])\s*(?:-|to|\b)\s*(p[1-9]|p1[0-3])?\b', cleaned)
    if period_match:
        start_p = period_match.group(1).upper()
        if period_match.group(2):
            end_p = period_match.group(2).upper()
        else:
            end_p = start_p
    else:
        # Hinglish / English vague times
        if any(w in cleaned for w in ["subah", "morning", "early"]):
            start_p, end_p = "P2", "P3"
        elif any(w in cleaned for w in ["dopahar", "afternoon", "post lunch"]):
            start_p, end_p = "P6", "P7"
        elif any(w in cleaned for w in ["shaam", "evening", "raat", "night"]):
            start_p, end_p = "P10", "P12"
        else:
            missing_fields.append("period_range")
            clarifying_question = "What time or period range do you need the venue for?"

    # 4. Attendance detection
    attendance = 50
    # First priority: explicit attendance noun
    att_explicit = re.search(r'\b(\d{2,4})\s*(?:people|students|attendees|participants|log|members|audience)\b', cleaned)
    if att_explicit:
        try:
            val = int(att_explicit.group(1))
            if 10 <= val <= 1000:
                attendance = val
        except ValueError:
            pass
    else:
        # Fallback: numbers not followed by time indicators
        for match in re.finditer(r'\b(\d{2,4})\b(?!\s*(?:baje|am|pm|o\'clock|hr|hours|h))', cleaned):
            try:
                val = int(match.group(1))
                if 20 <= val <= 1000:
                    attendance = val
                    break
            except ValueError:
                pass

    # 5. Title extraction
    title = "Venue Booking Request"
    if detected_room:
        title = f"Event Booking in {detected_room}"
    elif "hackathon" in cleaned:
        title = "Hackathon Booking"
    elif "guest" in cleaned:
        title = "Guest Lecture Session"
    elif "workshop" in cleaned:
        title = "Technical Workshop"

    return {
        "title": title,
        "day": detected_day,
        "start_period": start_p,
        "end_period": end_p,
        "preferred_room": detected_room,
        "required_room_type": required_room_type,
        "expected_attendance": attendance,
        "features_needed": ["projector"] if required_room_type in ["lecture_hall", "seminar_hall"] else [],
        "missing_fields": missing_fields,
        "clarifying_question": clarifying_question,
        "llm_used": False,
        "parser": "rule_based_fallback"
    }

def parse_schedule_intent_fallback(text: str, faculty_id: str) -> Dict[str, Any]:
    cleaned = sanitize_user_input(text).lower()
    
    # Check for leave or reschedule keywords
    is_leave = any(w in cleaned for w in ["leave", "chutti", "not available", "bimar", "sick", "absent", "bahar"])
    is_reschedule = any(w in cleaned for w in ["shift", "reschedule", "badal", "change", "move", "cancel"])

    # Day detection
    day = "Tue"
    for kw, d_val in DAYS_LEXICON.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
            if d_val == "TODAY":
                day = "Mon"
            elif d_val == "TOMORROW":
                day = "Tue"
            elif d_val == "DAY_AFTER_TOMORROW":
                day = "Wed"
            else:
                day = d_val
            break

    # Periods
    start_p = "P1"
    end_p = "P4"
    if "subah" in cleaned or "morning" in cleaned:
        start_p, end_p = "P1", "P4"
    elif "dopahar" in cleaned or "afternoon" in cleaned:
        start_p, end_p = "P6", "P9"

    return {
        "intent": "faculty_leave" if is_leave else "reschedule_request",
        "faculty_id": faculty_id,
        "day": day,
        "start_period": start_p,
        "end_period": end_p,
        "reason": text,
        "llm_used": False,
        "parser": "rule_based_fallback"
    }
