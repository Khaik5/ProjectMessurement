export default function EmptyState({ title = 'No analysis selected', description = 'Upload a dataset and run analysis to view results.' }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}
