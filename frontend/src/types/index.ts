export type UserRole = 'admin' | 'coordinator' | 'faculty' | 'club';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  department?: string;
}

export type DayOfWeek = 'MON' | 'TUE' | 'WED' | 'THU' | 'FRI';

export interface TimetableSession {
  session_id: string;
  course_code: string;
  course_name: string;
  type: 'LECTURE' | 'LAB' | 'TUTORIAL';
  group_id: string;
  faculty_id: string;
  room_id: string;
  day: DayOfWeek;
  start_period: number;
  duration: number;
  is_disrupted?: boolean;
  moved_from?: {
    day: DayOfWeek;
    start_period: number;
    room_id: string;
  };
}

export interface Room {
  room_id: string;
  name: string;
  building: string;
  floor: number;
  capacity: number;
  type: 'CLASSROOM' | 'LAB' | 'AUDITORIUM' | 'SEMINAR_HALL';
  features: string[];
  is_active: boolean;
}

export interface Faculty {
  faculty_id: string;
  name: string;
  department: string;
  designation: string;
  email: string;
  max_hours_per_day: number;
}

export interface StudentGroup {
  group_id: string;
  name: string;
  department: string;
  year: number;
  section: string;
  strength: number;
}

export interface Exam {
  exam_id: string;
  course_code: string;
  course_name: string;
  student_groups: string[];
  total_students: number;
  day: DayOfWeek;
  slot: 'MORNING' | 'AFTERNOON';
  rooms: string[];
  effective_capacities?: Record<string, number>;
}

export interface BookingRequest {
  request_id: string;
  title: string;
  requester_name: string;
  requester_role: string;
  requester_email: string;
  category: string;
  requested_room: string;
  day: DayOfWeek;
  start_period: number;
  duration: number;
  status: 'APPROVED' | 'ALTERNATIVE_OFFERED' | 'REJECTED' | 'PENDING';
  allocated_room?: string;
  allocated_day?: DayOfWeek;
  allocated_start_period?: number;
  score?: number;
  reason?: string;
  alternatives?: Array<{
    room_id: string;
    day: DayOfWeek;
    start_period: number;
    score: number;
  }>;
  created_at?: string;
}

export interface Disruption {
  disruption_id: string;
  type: 'FACULTY_LEAVE' | 'ROOM_CLOSURE' | 'EXTRA_SESSION';
  title: string;
  description: string;
  affected_faculty?: string;
  affected_room?: string;
  affected_days: DayOfWeek[];
  status: 'PENDING' | 'APPLIED' | 'REJECTED';
  moved_sessions_count?: number;
}

export interface AssistantProposal {
  action: 'BOOKING' | 'RESCHEDULE' | 'QUERY';
  title: string;
  parsed: Record<string, any>;
  feasible: boolean;
  explanation: string;
  hard_violations?: string[];
  recommended_slot?: {
    room_id: string;
    day: DayOfWeek;
    start_period: number;
  };
}

export interface SolverJob {
  job_id: string;
  type: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  progress: number;
  message: string;
  result?: any;
  started_at: string;
  completed_at?: string;
}

export interface DashboardStats {
  total_sessions: number;
  total_teaching_hours: number;
  total_faculty: number;
  total_rooms: number;
  room_utilization_rate: number;
  pending_bookings_count: number;
  active_disruptions_count: number;
  room_categories_utilization: Record<string, number>;
}
