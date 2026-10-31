import {
  User,
  TimetableSession,
  Room,
  Faculty,
  StudentGroup,
  Exam,
  BookingRequest,
  Disruption,
  AssistantProposal,
  DashboardStats,
  SolverJob
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class ApiService {
  private token: string | null = null;
  private onAuthError?: () => void;

  constructor() {
    this.token = localStorage.getItem('cit_token');
  }

  public setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('cit_token', token);
    } else {
      localStorage.removeItem('cit_token');
    }
  }

  public getToken(): string | null {
    return this.token;
  }

  public setOnAuthError(callback: () => void) {
    this.onAuthError = callback;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retries = 2
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        this.setToken(null);
        if (this.onAuthError) {
          this.onAuthError();
        }
        throw new Error('Unauthorized');
      }

      if (!response.ok) {
        let errorMsg = `HTTP Error ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) {
            errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {
          // fallback to status text
        }
        throw new Error(errorMsg);
      }

      return (await response.json()) as T;
    } catch (err: any) {
      if (retries > 0 && (err.name === 'TypeError' || err.message.includes('fetch'))) {
        // Cold-start retry
        await new Promise((resolve) => setTimeout(resolve, 2000));
        return this.request<T>(endpoint, options, retries - 1);
      }
      throw err;
    }
  }

  // Health
  public async checkHealth(): Promise<{ status: string; timestamp?: string }> {
    return this.request<{ status: string; timestamp?: string }>('/health', {}, 1);
  }

  // Auth
  public async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  public async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // Timetable
  public async getSchedule(): Promise<{ sessions: TimetableSession[]; metadata: any }> {
    return this.request<{ sessions: TimetableSession[]; metadata: any }>('/timetable/schedule');
  }

  public async getScheduleAfter(): Promise<{ sessions: TimetableSession[]; metadata: any; moved_sessions: any[] }> {
    return this.request<{ sessions: TimetableSession[]; metadata: any; moved_sessions: any[] }>('/timetable/schedule-after');
  }

  public async getSessions(params?: { group_id?: string; faculty_id?: string; room_id?: string }): Promise<TimetableSession[]> {
    const query = new URLSearchParams(params as any).toString();
    return this.request<TimetableSession[]>(`/timetable/sessions${query ? `?${query}` : ''}`);
  }

  public async explainSession(sessionId: string): Promise<{
    session_id: string;
    explanation: string;
    hard_constraints_satisfied: string[];
    soft_score_breakdown: Record<string, any>;
    alternative_slots_considered: number;
  }> {
    return this.request(`/timetable/explain?session_id=${sessionId}`);
  }

  // Datasets / Resources
  public async getRooms(): Promise<Room[]> {
    return this.request<Room[]>('/datasets/rooms');
  }

  public async getFaculty(): Promise<Faculty[]> {
    return this.request<Faculty[]>('/datasets/faculty');
  }

  public async getGroups(): Promise<StudentGroup[]> {
    return this.request<StudentGroup[]>('/datasets/groups');
  }

  public async findFreeRooms(params: {
    day: string;
    start_period: number;
    duration: number;
    min_capacity?: number;
    room_type?: string;
  }): Promise<{ available_rooms: Room[]; total_checked: number }> {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`/views/free-rooms?${query}`);
  }

  // Exams
  public async getExams(): Promise<Exam[]> {
    return this.request<Exam[]>('/exams');
  }

  // Bookings
  public async getBookings(): Promise<BookingRequest[]> {
    return this.request<BookingRequest[]>('/bookings');
  }

  public async createBooking(data: Partial<BookingRequest>): Promise<BookingRequest> {
    return this.request<BookingRequest>('/bookings', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  public async approveBooking(requestId: string): Promise<BookingRequest> {
    return this.request<BookingRequest>(`/bookings/${requestId}/approve`, {
      method: 'POST',
    });
  }

  public async rejectBooking(requestId: string, reason: string): Promise<BookingRequest> {
    return this.request<BookingRequest>(`/bookings/${requestId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  public async runSpectraEngine(): Promise<{ approved_count: number; rejected_count: number; total_score: number }> {
    return this.request('/bookings/run-spectra', {
      method: 'POST',
    });
  }

  // Rescheduling / Disruptions
  public async getDisruptions(): Promise<Disruption[]> {
    return this.request<Disruption[]>('/rescheduling/disruptions');
  }

  public async applySampleDisruption(): Promise<{
    status: string;
    moved_count: number;
    diffs: any[];
    violations: number;
  }> {
    return this.request('/rescheduling/apply-sample', {
      method: 'POST',
    });
  }

  public async applyCustomDisruption(data: any): Promise<any> {
    return this.request('/rescheduling/apply', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // AI Assistant
  public async askAssistant(message: string): Promise<AssistantProposal> {
    return this.request<AssistantProposal>('/assistant/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  // Manual moves
  public async validateManualMove(data: {
    session_id: string;
    new_day: string;
    new_start_period: number;
    new_room_id: string;
  }): Promise<{ is_valid: boolean; hard_violations: string[]; soft_penalty_delta: number }> {
    return this.request('/manual/validate-move', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  public async commitManualMove(data: {
    session_id: string;
    new_day: string;
    new_start_period: number;
    new_room_id: string;
  }): Promise<{ success: boolean; session: TimetableSession }> {
    return this.request('/manual/commit-move', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Dashboard
  public async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/dashboard/stats');
  }

  // Admin & Exports
  public async resetDemoData(): Promise<{ success: boolean; message: string }> {
    return this.request('/admin/reset-demo', {
      method: 'POST',
    });
  }

  public async getAuditLogs(): Promise<any[]> {
    return this.request<any[]>('/admin/audit-logs');
  }

  public async getExportJson(type: 'schedule' | 'schedule_after'): Promise<any> {
    return this.request(`/exports/${type}`);
  }
}

export const api = new ApiService();
