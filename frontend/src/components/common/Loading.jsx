export default function Loading({ label = 'Loading...', rows = 3, compact = false }) {
  return (
    <div className={`loading ${compact ? 'loading-compact' : ''}`}>
      <div className="loading-head">
        <span className="loading-spinner" />
        <strong>{label}</strong>
      </div>
      <div className="skeleton-stack">
        {Array.from({ length: rows }).map((_, index) => (
          <span className="skeleton-line" key={index} style={{ width: `${92 - index * 12}%` }} />
        ))}
      </div>
    </div>
  );
}
