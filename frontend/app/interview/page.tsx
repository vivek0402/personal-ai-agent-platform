'use client';

import { useState } from 'react';
import { generatePrepKit } from '@/lib/api';
import type { InterviewPrepResult } from '@/lib/types';

/* ── Spinner ─────────────────────────────────────────────────────────────────── */
function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4 text-white"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

/* ── Category badge helper ───────────────────────────────────────────────────── */
function categoryLabel(index: number) {
  if (index < 4) return { label: 'Behavioral',  cls: 'bg-purple-100 text-purple-700' };
  if (index < 8) return { label: 'Technical',   cls: 'bg-blue-100 text-blue-700' };
  return               { label: 'Situational',  cls: 'bg-orange-100 text-orange-700' };
}

/* ── Main page ───────────────────────────────────────────────────────────────── */
export default function InterviewPage() {
  const [company, setCompany]       = useState('');
  const [jdText, setJdText]         = useState('');
  const [resumeText, setResumeText] = useState('');
  const [result, setResult]         = useState<InterviewPrepResult | null>(null);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState<string | null>(null);
  const [expandedQ, setExpandedQ]   = useState<number | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!company || !jdText || !resumeText) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await generatePrepKit(company, jdText, resumeText);
      if (resp.success) {
        setResult(resp.data);
        setExpandedQ(0); // auto-open first question
      } else {
        setError(resp.error ?? 'Generation failed — check backend logs');
      }
    } catch {
      setError('Network error — make sure the backend is running on port 8000');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <h1 className="text-2xl font-bold text-slate-900 mb-1">Interview Prep</h1>
      <p className="text-sm text-slate-500 mb-8">
        3-step AI pipeline: company insights &rarr; 10 targeted questions &rarr; personalised SAR answers.
      </p>

      {/* ── Input Form (hidden after result) ──────────────────────────────────── */}
      {!result ? (
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Company */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Company
            </label>
            <input
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="e.g. Zepto, Google, Swiggy"
              className="w-full border border-slate-300 rounded-lg px-4 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {/* JD */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Job Description
            </label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the full job description here…"
              rows={9}
              className="w-full border border-slate-300 rounded-lg px-4 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none font-mono"
            />
          </div>

          {/* Resume */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Your Resume
            </label>
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              placeholder="Paste your resume text here…"
              rows={9}
              className="w-full border border-slate-300 rounded-lg px-4 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none font-mono"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || !company.trim() || !jdText.trim() || !resumeText.trim()}
            className="w-full bg-indigo-600 text-white py-3 rounded-xl text-sm font-semibold hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Spinner />
                Generating prep kit… (~15 seconds)
              </>
            ) : (
              'Generate Interview Prep Kit'
            )}
          </button>
        </form>
      ) : (
        /* ── Results ───────────────────────────────────────────────────────── */
        <div className="space-y-7">
          {/* Title row */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Prep Kit: {result.company}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Session ID: {result.session_id}
              </p>
            </div>
            <button
              onClick={() => { setResult(null); setExpandedQ(null); }}
              className="text-sm text-indigo-600 hover:text-indigo-800 font-medium border border-indigo-200 hover:border-indigo-400 px-3 py-1.5 rounded-lg transition-colors"
            >
              Start over
            </button>
          </div>

          {/* Company Insights Card */}
          <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-6">
            <h3 className="text-xs font-bold text-indigo-700 uppercase tracking-widest mb-4">
              Company Insights
            </h3>
            <pre className="text-sm text-indigo-900 whitespace-pre-wrap font-sans leading-relaxed">
              {result.insights}
            </pre>
          </div>

          {/* Q&A Accordion */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-slate-900 text-sm">
                10 Interview Questions + Personalised SAR Answers
              </h3>
              <button
                onClick={() => setExpandedQ(null)}
                className="text-xs text-slate-400 hover:text-slate-600"
              >
                Collapse all
              </button>
            </div>

            <div className="space-y-2">
              {result.questions.map((q, i) => {
                const cat = categoryLabel(i);
                const open = expandedQ === i;
                return (
                  <div
                    key={i}
                    className="border border-slate-200 rounded-xl overflow-hidden bg-white"
                  >
                    <button
                      onClick={() => setExpandedQ(open ? null : i)}
                      className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-slate-50 transition-colors"
                    >
                      {/* Q number */}
                      <span className="shrink-0 text-xs font-bold text-indigo-600 bg-indigo-50 rounded-full w-7 h-7 flex items-center justify-center mt-0.5">
                        Q{i + 1}
                      </span>
                      {/* Question + category */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${cat.cls}`}>
                            {cat.label}
                          </span>
                        </div>
                        <span className="text-sm text-slate-900 font-medium leading-snug">
                          {q}
                        </span>
                      </div>
                      {/* Chevron */}
                      <span className="shrink-0 text-slate-400 text-xs mt-1">
                        {open ? '▲' : '▼'}
                      </span>
                    </button>

                    {open && (
                      <div className="px-4 pb-4 pt-0 border-t border-slate-100 bg-slate-50">
                        <div className="flex gap-2 mt-3">
                          <span className="shrink-0 text-xs font-bold text-slate-400 w-7 text-center mt-0.5">
                            A
                          </span>
                          <p className="text-sm text-slate-700 leading-relaxed">
                            {result.answers[i]}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
