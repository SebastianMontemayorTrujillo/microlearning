"use client";
export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="empty-state">
      <h1>A little interruption.</h1>
      <p>
        We couldn’t open this view. Your saved progress is still in the
        database.
      </p>
      <button className="primary-button" onClick={reset}>
        Try again
      </button>
    </main>
  );
}
