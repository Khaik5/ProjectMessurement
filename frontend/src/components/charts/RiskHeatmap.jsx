import EmptyState from '../common/EmptyState.jsx';
import { riskClass, riskFromProbability } from '../../utils/riskUtils.js';
import { fmtPercent } from '../../utils/formatters.js';

export default function RiskHeatmap({ data = [] }) {
  const rows = Array.isArray(data)
    ? data
    : (Array.isArray(data?.rows)
      ? data.rows
      : (Array.isArray(data?.heatmap)
        ? data.heatmap.map((item) => ({
          module_name: item.x,
          defect_probability: item.value,
          risk_level: item.risk_level
        }))
        : []));
  if (!rows.length) return <EmptyState title="No risk heatmap" />;
  const columns = [
    ['Size', 'size_score'],
    ['Complexity', 'complexity_score'],
    ['Coupling', 'coupling_score'],
    ['Churn', 'churn_score'],
    ['Final Probability', 'defect_probability']
  ];
  return (
    <div className="matrix-wrap">
      <div className="matrix-row matrix-head">
        <span>Module</span>
        {columns.map(([label]) => <span key={label}>{label}</span>)}
      </div>
      {rows.slice(0, 30).map((item) => (
        <div key={`${item.module_name}-${item.defect_probability}`} className="matrix-row">
          <strong>{item.module_name}</strong>
          {columns.map(([label, key]) => (
            <span key={`${item.module_name}-${key}`} className={`heat-cell ${riskClass(key === 'defect_probability' ? item.risk_level : riskFromProbability(item[key]))}`} style={{ opacity: 0.55 + Math.min(Number(item[key] || 0), 1) * 0.45 }}>
              {fmtPercent(item[key])}
            </span>
          ))}
        </div>
      ))}
    </div>
  );
}
