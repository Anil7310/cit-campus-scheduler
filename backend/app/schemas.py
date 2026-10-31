from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# Auth schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department: str
    faculty_id: Optional[str] = None
    is_active: bool

# Timetable schemas
class SessionAssignment(BaseModel):
    session_id: str
    day: str
    start_period: str
    room_id: str

class TimetableGenerateRequest(BaseModel):
    time_limit_seconds: Optional[int] = None
    auto_publish: bool = False

# Booking schemas
class BookingCreateRequest(BaseModel):
    title: str
    category: str = Field(description="institute_event | guest_lecture | department_event | club_event")
    day: str
    start_period: str
    end_period: str
    preferred_room: Optional[str] = None
    required_room_type: str
    expected_attendance: int
    features_needed: List[str] = []
    original_text: Optional[str] = None

class BookingDecisionRequest(BaseModel):
    decision: str = Field(description="approved | rejected | alternative_offered")
    assigned_room: Optional[str] = None
    reason: str
    alternative: Optional[Dict[str, Any]] = None

# Rescheduling & Disruption schemas
class DisruptionItem(BaseModel):
    id: Optional[str] = None
    type: str = Field(description="faculty_leave | room_closure | new_session")
    faculty_id: Optional[str] = None
    room_id: Optional[str] = None
    day: Optional[str] = None
    start_period: Optional[str] = None
    end_period: Optional[str] = None
    session: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None

class DisruptionProposalCreate(BaseModel):
    disruptions: List[DisruptionItem]

# Manual assignment schemas
class ManualAssignmentRequest(BaseModel):
    session_id: str
    day: str
    start_period: str
    room_id: str
    dry_run: bool = False

# Assistant schemas
class AssistantParseRequest(BaseModel):
    message: str

class AssistantScheduleRequest(BaseModel):
    message: str

class ResetDemoRequest(BaseModel):
    confirm: str
