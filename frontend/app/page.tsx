import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="max-w-4xl mx-auto py-16 px-4 text-center">
      <h1 className="text-4xl font-bold text-slate-900 mb-4">
        Personal AI Agent Platform
      </h1>
      <p className="text-lg text-slate-500 mb-12 max-w-2xl mx-auto">
        Two intelligent agents to help you stay organised and land your next
        role — powered by Groq and llama3-70b-8192.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
        {/* Task Manager Card */}
        <Link
          href="/tasks"
          className="group block bg-white rounded-2xl border border-slate-200 p-7 hover:shadow-md hover:border-indigo-200 transition-all"
        >
          <div className="text-3xl mb-4">📋</div>
          <h2 className="text-xl font-semibold text-slate-900 mb-2 group-hover:text-indigo-600 transition-colors">
            Task Manager
          </h2>
          <p className="text-sm text-slate-500 leading-relaxed">
            Add tasks in plain English. The AI extracts title, due date, and
            priority automatically. Reminders fire 24h or 6h before due date.
          </p>
          <div className="mt-5 text-sm font-medium text-indigo-600">
            Open Task Manager &rarr;
          </div>
        </Link>

        {/* Interview Prep Card */}
        <Link
          href="/interview"
          className="group block bg-white rounded-2xl border border-slate-200 p-7 hover:shadow-md hover:border-indigo-200 transition-all"
        >
          <div className="text-3xl mb-4">🎯</div>
          <h2 className="text-xl font-semibold text-slate-900 mb-2 group-hover:text-indigo-600 transition-colors">
            Interview Prep
          </h2>
          <p className="text-sm text-slate-500 leading-relaxed">
            Paste a JD and your resume. Get company insights, 10 targeted
            questions, and personalised SAR answers grounded in your real
            projects.
          </p>
          <div className="mt-5 text-sm font-medium text-indigo-600">
            Start Prep Kit &rarr;
          </div>
        </Link>
      </div>

      {/* Quick stats row */}
      <div className="mt-16 grid grid-cols-3 gap-4 text-center border-t border-slate-200 pt-10">
        <div>
          <div className="text-2xl font-bold text-indigo-600">llama3-70b</div>
          <div className="text-xs text-slate-500 mt-1">LLM via Groq</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-indigo-600">10</div>
          <div className="text-xs text-slate-500 mt-1">targeted questions per prep kit</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-indigo-600">SAR</div>
          <div className="text-xs text-slate-500 mt-1">Situation-Action-Result answers</div>
        </div>
      </div>
    </div>
  );
}
