'use client';

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 min-h-screen flex items-center justify-center">
        <div className="text-center px-4">
          <div className="text-5xl mb-6">💥</div>
          <h2 className="text-xl font-semibold text-slate-900 mb-3">
            Critical application error
          </h2>
          <p className="text-sm text-slate-500 mb-8">
            The application encountered an unrecoverable error.
          </p>
          <button
            onClick={reset}
            className="bg-indigo-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            Reload application
          </button>
        </div>
      </body>
    </html>
  );
}
