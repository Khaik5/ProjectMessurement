import { AlertTriangle } from 'lucide-react';
import { fmtPercent } from '../../utils/formatters.js';

export default function AlertPanel({ items = [] }) {
  const critical = items.filter((item) => ['HIGH', 'CRITICAL'].includes(item.risk_level)).slice(0, 3);
  if (!critical.length) return null;
  return (
    <div className="alert-panel">
      <AlertTriangle />
      <div>
        <strong>Recent Critical Alerts</strong>
        {critical.map((item) => (
          <p key={`${item.module_name}-${item.defect_probability}`}>{item.module_name}: {fmtPercent(item.defect_probability)} probability</p>
        ))}
      </div>
    </div>
  );
}
