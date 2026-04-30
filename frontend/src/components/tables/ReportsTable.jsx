import EmptyState from '../common/EmptyState.jsx';
import { fmtDate } from '../../utils/formatters.js';

export default function ReportsTable({ rows = [], selected = [], onSelect, selectable = false }) {
  if (!rows.length) return <EmptyState title="No reports" description="Generate a report after predictions exist." />;
  function toggle(id) {
    if (!onSelect) return;
    onSelect(selected.includes(id) ? selected.filter((item) => item !== id) : [...selected, id]);
  }
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{selectable ? <th></th> : null}<th>ID</th><th>Title</th><th>Project</th><th>Created</th><th>File</th></tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              {selectable ? <td><input type="checkbox" checked={selected.includes(row.id)} onChange={() => toggle(row.id)} /></td> : null}
              <td>#DFT-{String(row.id).padStart(4, '0')}</td>
              <td>{row.title}</td>
              <td>{row.project_id}</td>
              <td>{fmtDate(row.created_at)}</td>
              <td>{row.file_path || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
