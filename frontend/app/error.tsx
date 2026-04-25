'use client';

import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Page error:', error);
  }, [error]);

  return (
    <div className="max-w-4xl mx-auto py-20 px-4 text-center">
      <div className="text-5xl mb-6">⚠️</div>
      <h2 className="text-xl font-semibold text-slate-900 mb-3">
        Something went wrong
      </h2>
      <p className="text-sm text-slate-500 mb-8 max-w-md mx-auto">
        An unexpected error occurred. Your data is safe — the backend is likely
        unreachable or the AI service timed out.
      </p>
      <div className="flex gap-3 justify-center">
        <button
          onClick={reset}
          className="bg-indigo-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          Try again
        </button>
        <a
          href="/"
          className="border border-slate-300 text-slate-700 px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
        >
          Go home
        </a>
      </div>
      {process.env.NODE_ENV === 'development' && (
        <details className="mt-8 text-left max-w-xl mx-auto">
          <summary className="text-xs text-slate-400 cursor-pointer">
            Error details (dev only)
          </summary>
          <pre className="mt-2 text-xs text-red-600 bg-red-50 p-3 rounded-lg overflow-auto">
            {error.message}
            {error.stack && `\n\n${error.stack}`}
          </pre>
        </details>
      )}
    </div>
  );
}
