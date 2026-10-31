import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

PERIODS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11", "P12", "P13"]
TEACHING_PERIODS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]
PERIOD_INDEX = {p: i for i, p in enumerate(PERIODS)}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

@dataclass
class Room:
    id: str
    name: str
    type: str
    capacity: int
    accessible: bool
    features: List[str] = field(default_factory=list)
    maintenance_windows: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Faculty:
    id: str
    name: str
    department: str
    daily_limit_hours: int = 4
    unavailability: List[Dict[str, Any]] = field(default_factory=list)
    avoid_periods: List[str] = field(default_factory=list)

@dataclass
class StudentGroup:
    id: str
    name: str
    year: int
    size: int
    accessible_required: bool = False

@dataclass
class Course:
    code: str
    name: str
    department: str
    year: int
    credits: int

@dataclass
class Session:
    id: str
    course_code: str
    session_type: str
    duration_hours: int
    required_room_type: str
    student_groups: List[str]
    faculty_ids: List[str]
    accessible_required: bool = False
    elective_basket: Optional[str] = None
    fixed_slot: Optional[Dict[str, str]] = None

@dataclass
class Exam:
    id: str
    course_code: str
    student_groups: List[str]
    student_count: int
    duration_hours: int = 2
    preferred_room_types: List[str] = field(default_factory=list)

@dataclass
class BookingRequest:
    id: str
    requester_name: str
    requester_role: str
    category: str
    title: str
    original_text: str
    day: str
    start_period: str
    end_period: str
    preferred_room: Optional[str] = None
    required_room_type: str = "classroom"
    expected_attendance: int = 50
    features_needed: List[str] = field(default_factory=list)
    status: str = "pending"

class Dataset:
    def __init__(self, raw_data: Dict[str, Any]):
        self.raw = raw_data
        self.metadata = raw_data.get("metadata", {})
        
        self.rooms: List[Room] = [
            Room(**{k: v for k, v in r.items() if k in Room.__annotations__})
            for r in raw_data.get("rooms", [])
        ]
        self.rooms_by_id: Dict[str, Room] = {r.id: r for r in self.rooms}

        self.faculty: List[Faculty] = [
            Faculty(**{k: v for k, v in f.items() if k in Faculty.__annotations__})
            for f in raw_data.get("faculty", [])
        ]
        self.faculty_by_id: Dict[str, Faculty] = {f.id: f for f in self.faculty}

        self.student_groups: List[StudentGroup] = [
            StudentGroup(**{k: v for k, v in g.items() if k in StudentGroup.__annotations__})
            for g in raw_data.get("student_groups", [])
        ]
        self.groups_by_id: Dict[str, StudentGroup] = {g.id: g for g in self.student_groups}

        self.courses: List[Course] = [
            Course(**{k: v for k, v in c.items() if k in Course.__annotations__})
            for c in raw_data.get("courses", [])
        ]
        self.courses_by_code: Dict[str, Course] = {c.code: c for c in self.courses}

        self.sessions: List[Session] = [
            Session(**{k: v for k, v in s.items() if k in Session.__annotations__})
            for s in raw_data.get("sessions", [])
        ]
        self.sessions_by_id: Dict[str, Session] = {s.id: s for s in self.sessions}

        self.exams: List[Exam] = [
            Exam(**{k: v for k, v in e.items() if k in Exam.__annotations__})
            for e in raw_data.get("exams", [])
        ]
        self.exams_by_id: Dict[str, Exam] = {e.id: e for e in self.exams}

        self.booking_requests: List[BookingRequest] = [
            BookingRequest(**{k: v for k, v in b.items() if k in BookingRequest.__annotations__})
            for b in raw_data.get("booking_requests", [])
        ]
        self.bookings_by_id: Dict[str, BookingRequest] = {b.id: b for b in self.booking_requests}

def load_default_dataset() -> Dataset:
    # Look in backend seed_data, data/, or starter-pack/
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "seed_data", "cit_public.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "cit_public.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "starter-pack", "cit_public.json"),
        "data/cit_public.json",
        "starter-pack/cit_public.json"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Dataset(data)
    raise FileNotFoundError("cit_public.json could not be found in any expected location.")
