export interface Task {
  id: string;
  title: string;
  description?: string | null;
  due_date?: string | null;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'in_progress' | 'done';
  created_at: string;
  reminded_at?: string | null;
  confirmation_message?: string;
}

export interface InterviewPrepResult {
  session_id: string;
  company: string;
  insights: string;
  questions: string[];
  answers: string[];
}

export interface ResumeRecord {
  id: string;
  raw_text: string;
  uploaded_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error: string | null;
}
