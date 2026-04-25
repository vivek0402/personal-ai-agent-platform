import type { ApiResponse, Task, InterviewPrepResult, ResumeRecord } from './types';

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000';

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<ApiResponse<T>> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  return res.json() as Promise<ApiResponse<T>>;
}

// ── Tasks ─────────────────────────────────────────────────────────────────────

export function createTask(user_input: string) {
  return request<Task>('/api/tasks', {
    method: 'POST',
    body: JSON.stringify({ user_input }),
  });
}

export function listTasks(status?: string) {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  return request<Task[]>(`/api/tasks${qs}`);
}

export function updateTaskStatus(id: string, status: string) {
  return request<Task>(`/api/tasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

export function deleteTask(id: string) {
  return request<{ deleted: boolean; id: string }>(`/api/tasks/${id}`, {
    method: 'DELETE',
  });
}

// ── Interview ─────────────────────────────────────────────────────────────────

export function generatePrepKit(
  company: string,
  jd_text: string,
  resume_text: string,
) {
  return request<InterviewPrepResult>('/api/interview/prep', {
    method: 'POST',
    body: JSON.stringify({ company, jd_text, resume_text }),
  });
}

export function uploadResume(raw_text: string) {
  return request<ResumeRecord>('/api/interview/resume', {
    method: 'POST',
    body: JSON.stringify({ raw_text }),
  });
}

export function listSessions(company?: string) {
  const qs = company ? `?company=${encodeURIComponent(company)}` : '';
  return request<Array<Record<string, unknown>>>(`/api/interview/sessions${qs}`);
}
