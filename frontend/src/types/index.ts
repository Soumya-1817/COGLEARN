// User & Auth
export type UserRole = 'platform_admin' | 'inst_admin' | 'teacher' | 'student';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  institution_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Institution {
  id: string;
  name: string;
  slug: string;
  is_demo: boolean;
  is_active: boolean;
  approved_at: string | null;
  created_at?: string;
  student_count?: number;
  teacher_count?: number;
}

export interface Department {
  id: string;
  institution_id: string;
  name: string;
  code: string;
  created_at?: string;
}

export interface Programme {
  id: string;
  department_id: string;
  name: string;
  code: string;
  duration_years: number;
}

export interface Semester {
  id: string;
  institution_id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
}

// Academic structure
export interface Course {
  id: string;
  title: string;
  description: string;
  teacher_id: string;
  teacher_name?: string;
  semester_id: string;
  department_id: string;
  is_published: boolean;
  created_at: string;
  enrolled_count?: number;
  modules?: Module[];
}

export interface Module {
  id: string;
  course_id: string;
  title: string;
  order_index: number;
  lessons: Lesson[];
}

export interface Lesson {
  id: string;
  module_id?: string;
  title: string;
  lesson_type: 'video' | 'pdf' | 'text' | 'external';
  content_url: string;
  duration_minutes: number;
  is_published: boolean;
  order_index?: number;
}

export interface Assignment {
  id: string;
  course_id: string;
  course_title?: string;
  title: string;
  description: string;
  due_date: string;
  estimated_hours: number;
  workload_weight: number;
  is_published: boolean;
  submissions_count?: number;
  created_at?: string;
}

// Academic Task Queue
export type TaskType = 'assignment' | 'quiz' | 'assessment';
export type TaskStatus = 'pending' | 'active' | 'completed' | 'overdue' | 'cancelled';

export interface AcademicTask {
  id: string;
  student_id: string;
  course_id: string;
  course_title?: string;
  task_type: TaskType;
  title: string;
  description: string | null;
  arrival_timestamp: string;
  queue_position: number; // FIFO position
  due_date: string;
  estimated_workload: number;
  workload_weight: number;
  status: TaskStatus;
  is_overdue: boolean;
}

// Calendar
export interface CalendarEvent {
  id: string;
  event_type: string;
  title: string;
  start_datetime: string;
  end_datetime: string | null;
  is_revised: boolean;
  original_datetime: string | null;
  source_task_id: string | null;
}

// Notifications
export type NotificationPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Notification {
  id: string;
  category: string;
  title: string;
  body: string;
  priority: NotificationPriority;
  is_read: boolean;
  created_at: string;
  action_url: string | null;
}

// Mentor analytics (NEVER shown to students)
export type RiskZone = 'green' | 'yellow' | 'red';
export type DominantCognitiveState = 'underload' | 'flow' | 'overload' | 'fatigue';

export interface StudentAnalytics {
  student_id: string;
  student_name: string;
  email?: string;
  // IORI (mentor-only)
  latest_iori: number;
  risk_zone: RiskZone;
  iori_history: { date: string; iori: number }[];
  // M/M/1 queue
  latest_rho: number;
  is_stable: boolean;
  queue_length: number | null;
  // Workload
  pending_tasks: number;
  overdue_tasks: number;
  total_weighted_workload: number;
  // Model 4 dominant state
  dominant_state: DominantCognitiveState;
  // Probabilities (mentor-only, NOT for students)
  p_underload: number;
  p_flow: number;
  p_overload: number;
  p_fatigue: number;
  // Provisional parameters note
  is_provisional?: boolean;
}

// Student dashboard (safe - no cognitive internals)
export interface StudentDashboardData {
  pending_tasks: number;
  overdue_tasks: number;
  completed_tasks: number;
  next_deadline: { title: string; due_date: string } | null;
  upcoming_events: CalendarEvent[];
  unread_notifications: number;
  // NO iori, NO rho, NO hmm_probabilities
}

// Intervention & Mentorship
export interface Intervention {
  id: string;
  student_id: string;
  student_name: string;
  trigger_type: string;
  iori_value_at_trigger: number | null;
  risk_zone: string | null;
  status: 'open' | 'in_progress' | 'closed';
  created_at: string;
  notes?: string;
}

export interface MentorMessage {
  id: string;
  intervention_id?: string;
  sender_id: string;
  sender_name: string;
  body: string;
  sent_at: string;
  is_read: boolean;
}

export interface MentorshipRequest {
  id: string;
  student_id: string;
  student_name: string;
  course_id?: string;
  course_title?: string;
  reason: string;
  status: 'pending' | 'accepted' | 'declined' | 'completed';
  created_at: string;
}

// Institutional Analytics
export interface DepartmentAnalytics {
  department_id: string;
  department_name: string;
  student_count: number;
  avg_iori: number;
  iori_distribution: { green: number; yellow: number; red: number };
  intervention_count: number;
  avg_workload: number;
  suppressed: boolean; // true if below MIN_COHORT_SIZE
}

export interface InstitutionalAnalytics {
  total_students: number;
  total_teachers: number;
  total_courses: number;
  avg_institution_iori: number;
  iori_summary: { green: number; yellow: number; red: number };
  intervention_volume: { month: string; count: number }[];
  departments: DepartmentAnalytics[];
  cohort_size_suppressed: boolean;
}

// WebSocket Feed
export interface IoriAlert {
  student_id: string;
  student_name: string;
  iori: number;
  risk_zone: RiskZone;
  timestamp: string;
  dominant_state?: DominantCognitiveState;
}
