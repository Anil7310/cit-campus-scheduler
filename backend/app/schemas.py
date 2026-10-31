from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field

# Auth schemas
class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    password: str

class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    name: str = Field(min_length=2)
    email: Optional[str] = None
    role: str = Field(description="admin | coordinator | faculty | club")
    department: str = Field(default="CSE")
    faculty_id: Optional[str] = None
    qualifications: Optional[List[str]] = None
    fields_of_interest: Optional[List[str]] = None
    password: str = Field(min_length=4)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    name: str
    username: Optional[str] = None
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
    title: Optional[str] = None
    event_name: Optional[str] = None
    category: Optional[str] = "club_event"
    day: str
    start_period: Union[int, str]
    end_period: Optional[Union[int, str]] = None
    duration: Optional[int] = 1
    preferred_room: Optional[str] = None
    requested_room: Optional[str] = None
    required_room_type: Optional[str] = "classroom"
    expected_attendance: Optional[int] = 50
    features_needed: List[str] = []
    original_text: Optional[str] = None
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    requester_role: Optional[str] = None

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
