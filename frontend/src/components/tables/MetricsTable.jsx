import Badge from '../common/Badge.jsx';
import EmptyState from '../common/EmptyState.jsx';
import { fmtDate, fmtPercent } from '../../utils/formatters.js';
import { predictionClass, riskFromProbability } from '../../utils/riskUtils.js';

export default function MetricsTable({ rows = [] }) {
  if (!rows.length) return <EmptyState title="No metrics or predictions" description="Upload a dataset and run analysis." />;
  const hasPredictions = rows.some((row) => row.defect_probability !== undefined && row.defect_probability !== null);
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Module</th>
            <th>LOC</th>
            <th>NCLOC</th>
            <th>CLOC</th>
            <th>KLOC</th>
            <th>Complexity</th>
            <th>Coupling</th>
            <th>Churn</th>
            <th>Defect Density</th>
            <th>Size Score</th>
            <th>Complexity Score</th>
            <th>Coupling Score</th>
            <th>Churn Score</th>
            <th>Measurement Risk</th>
            {hasPredictions ? <th>Prediction Label</th> : null}
            {hasPredictions ? <th>Defect Probability</th> : null}
            {hasPredictions ? <th>Risk</th> : null}
            {hasPredictions ? <th>Model Used</th> : null}
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const level = row.risk_level || riskFromProbability(row.defect_probability);
            const label = row.prediction_label || (row.prediction === 1 ? 'Defect' : row.prediction === 0 ? 'No Defect' : '-');
            return (
              <tr key={`${row.module_name}-${index}`}>
                <td><strong>{row.module_name}</strong></td>
                <td>{row.loc}</td>
                <td>{row.ncloc ?? '-'}</td>
                <td>{row.cloc ?? '-'}</td>
                <td>{Number(row.kloc || 0).toFixed(3)}</td>
                <td>{row.complexity}</td>
                <td>{row.coupling}</td>
                <td>{row.code_churn}</td>
                <td>{row.defect_density !== undefined && row.defect_density !== null ? Number(row.defect_density).toFixed(3) : '-'}</td>
                <td>{fmtPercent(row.size_score)}</td>
                <td>{fmtPercent(row.complexity_score)}</td>
                <td>{fmtPercent(row.coupling_score)}</td>
                <td>{fmtPercent(row.churn_score)}</td>
                <td>{fmtPercent(row.risk_score)}</td>
                {hasPredictions ? <td><span className={`badge ${predictionClass(label)}`}>{label}</span></td> : null}
                {hasPredictions ? (
                  <td>
                    {row.defect_probability !== undefined ? (
                      <div className="probability-cell">
                        <span>{fmtPercent(row.defect_probability)}</span>
                        <div><i style={{ width: `${Math.min(Math.max(Number(row.defect_probability || 0), 0), 1) * 100}%` }} /></div>
                      </div>
                    ) : '-'}
                  </td>
                ) : null}
                {hasPredictions ? <td><Badge level={level}>{level}</Badge></td> : null}
                {hasPredictions ? <td>{row.model_source || row.model_used || (row.model_id ? 'AI production model' : 'Measurement fallback')}</td> : null}
                <td>{fmtDate(row.created_at || row.timestamp || row.recorded_at)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
