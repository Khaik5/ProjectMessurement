import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import EmptyState from '../common/EmptyState.jsx';
import { fmtPercent } from '../../utils/formatters.js';

export default function ModelComparisonChart({ data = [] }) {
  if (!data.length) return <EmptyState title="No model comparison" description="Train models to populate MLModels and TrainingRuns." />;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="model" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
        <Tooltip formatter={(v) => fmtPercent(v)} />
        <Legend />
        <Bar dataKey="accuracy" fill="#0b1930" />
        <Bar dataKey="precision" fill="#64748b" />
        <Bar dataKey="recall" fill="#ffb020" />
        <Bar dataKey="f1_score" fill="#ff7a00" />
      </BarChart>
    </ResponsiveContainer>
  );
}
