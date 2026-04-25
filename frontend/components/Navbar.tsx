import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-40 bg-white border-b border-slate-200">
      <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="text-sm font-semibold text-slate-900 hover:text-indigo-600 transition-colors"
        >
          AI Agent Platform
        </Link>
        <div className="flex gap-6 text-sm">
          <Link
            href="/tasks"
            className="text-slate-600 hover:text-indigo-600 transition-colors font-medium"
          >
            Tasks
          </Link>
          <Link
            href="/interview"
            className="text-slate-600 hover:text-indigo-600 transition-colors font-medium"
          >
            Interview Prep
          </Link>
        </div>
      </div>
    </nav>
  );
}
