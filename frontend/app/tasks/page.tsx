'use client';

import { useState, useEffect, useCallback } from 'react';
import { createTask, listTasks, updateTaskStatus, deleteTask } from '@/lib/api';
import type { Task } from '@/lib/types';

/* ── Toast ──────────────────────────────────────────────────────────────────── */
interface Toast {
  id: number;
  message: string;
  type: 'success' | 'error';
}

function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const add = useCallback((message: string, type: Toast['type'] = 'success') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500);
  }, []);
  return { toasts, add };
}

/* ── Priority badge ─────────────────────────────────────────────────────────── */
const PRIORITY_CLASSES: Record<string, string> = {
  high:   'bg-red-100 text-red-700 border border-red-200',
  medium: 'bg-yellow-100 text-yellow-700 border border-yellow-200',
  low:    'bg-green-100 text-green-700 border border-green-200',
};

function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
        PRIORITY_CLASSES[priority] ?? 'bg-slate-100 text-slate-600'
      }`}
    >
      {priority}
    </span>
  );
}

/* ── Main page ───────────────────────────────────────────────────────────────── */
export default function TasksPage() {
  const [tasks, setTasks]       = useState<Task[]>([]);
  const [input, setInput]       = useState('');
  const [loading, setLoading]   = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const { toasts, add: addToast } = useToast();

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await listTasks();
      if (resp.success) setTasks(resp.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  /* create */
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    setSubmitting(true);
    try {
      const resp = await createTask(input.trim());
      if (resp.success) {
        setInput('');
        addToast(`Created: "${resp.data.title}"`);
        fetchTasks();
      } else {
        addToast(resp.error ?? 'Failed to create task', 'error');
      }
    } catch {
      addToast('Network error — backend offline?', 'error');
    } finally {
      setSubmitting(false);
    }
  }

  /* mark done */
  async function handleDone(id: string, title: string) {
    const resp = await updateTaskStatus(id, 'done');
    if (resp.success) {
      addToast(`Marked done: "${title}"`);
      fetchTasks();
    } else {
      addToast(resp.error ?? 'Update failed', 'error');
    }
  }

  /* delete */
  async function handleDelete(id: string, title: string) {
    const resp = await deleteTask(id);
    if (resp.success) {
      addToast(`Deleted: "${title}"`);
      fetchTasks();
    } else {
      addToast(resp.error ?? 'Delete failed', 'error');
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <h1 className="text-2xl font-bold text-slate-900 mb-1">Task Manager</h1>
      <p className="text-sm text-slate-500 mb-6">
        Type a task in plain English — the AI extracts title, due date, and priority.
      </p>

      {/* Input form */}
      <form onSubmit={handleSubmit} className="flex gap-3 mb-8">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`e.g. "Apply to Zepto by this Friday, high priority"`}
          className="flex-1 border border-slate-300 rounded-lg px-4 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          disabled={submitting}
        />
        <button
          type="submit"
          disabled={submitting || !input.trim()}
          className="bg-indigo-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
        >
          {submitting ? 'Saving…' : 'Add Task'}
        </button>
      </form>

      {/* Task table */}
      {loading ? (
        <div className="text-center py-16 text-slate-400 text-sm">Loading tasks…</div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-16 text-slate-400 border-2 border-dashed border-slate-200 rounded-2xl">
          <div className="text-3xl mb-3">📋</div>
          <div className="text-sm">No tasks yet. Add your first one above.</div>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-slate-600 text-left border-b border-slate-200">
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Due Date</th>
                <th className="px-4 py-3 font-medium">Priority</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {tasks.map((task) => (
                <tr
                  key={task.id}
                  className={`transition-colors hover:bg-slate-50 ${
                    task.status === 'done' ? 'opacity-60' : ''
                  }`}
                >
                  <td className="px-4 py-3 text-slate-900 font-medium max-w-xs">
                    <span className={task.status === 'done' ? 'line-through' : ''}>
                      {task.title}
                    </span>
                    {task.description && (
                      <div className="text-xs text-slate-400 mt-0.5 font-normal truncate">
                        {task.description}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                    {task.due_date ?? <span className="text-slate-300">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    <PriorityBadge priority={task.priority} />
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs font-medium ${
                        task.status === 'done'
                          ? 'text-green-600'
                          : task.status === 'in_progress'
                          ? 'text-blue-600'
                          : 'text-slate-500'
                      }`}
                    >
                      {task.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      {task.status !== 'done' && (
                        <button
                          onClick={() => handleDone(task.id, task.title)}
                          className="text-xs text-green-700 border border-green-200 bg-green-50 hover:bg-green-100 px-2.5 py-1 rounded-md transition-colors"
                        >
                          Done
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(task.id, task.title)}
                        className="text-xs text-red-700 border border-red-200 bg-red-50 hover:bg-red-100 px-2.5 py-1 rounded-md transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Toasts */}
      <div className="fixed bottom-5 right-5 flex flex-col gap-2 z-50 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`px-4 py-3 rounded-xl shadow-lg text-sm font-medium text-white max-w-xs ${
              t.type === 'success' ? 'bg-green-600' : 'bg-red-600'
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </div>
  );
}
