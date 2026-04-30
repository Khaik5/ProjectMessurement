import EmptyState from '../common/EmptyState.jsx';
import { fmtDate } from '../../utils/formatters.js';

export default function AuditLogTable({ rows = [] }) {
  if (!rows.length) return <EmptyState title="No audit logs" description="System actions will appear here." />;
  return (
    <div className="audit-list">
      {rows.map((row) => (
        <div key={row.id} className="audit-item">
          <strong>{row.action}</strong>
          <span>{row.entity_type || 'System'} #{row.entity_id || '-'} - {fmtDate(row.created_at)}</span>
        </div>
      ))}
    </div>
  );
}
