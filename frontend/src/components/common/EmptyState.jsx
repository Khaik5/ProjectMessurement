import { Inbox } from 'lucide-react';

export default function EmptyState({
  title = 'No data',
  description = 'Run an action to populate this view.',
  action = null
}) {
  return (
    <div className="empty-state">
      <div className="empty-icon"><Inbox size={22} /></div>
      <strong>{title}</strong>
      {description ? <p>{description}</p> : null}
      {action ? <div className="empty-action">{action}</div> : null}
    </div>
  );
}
