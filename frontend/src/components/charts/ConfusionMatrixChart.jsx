import EmptyState from '../common/EmptyState.jsx';

export default function ConfusionMatrixChart({ matrix }) {
  if (!matrix) return <EmptyState title="No confusion matrix" />;
  const cells = [
    ['TN', matrix?.[0]?.[0] ?? 0],
    ['FP', matrix?.[0]?.[1] ?? 0],
    ['FN', matrix?.[1]?.[0] ?? 0],
    ['TP', matrix?.[1]?.[1] ?? 0]
  ];
  return (
    <div className="matrix-grid">
      {cells.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}
