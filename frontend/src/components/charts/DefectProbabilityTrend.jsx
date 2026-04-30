import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import EmptyState from '../common/EmptyState.jsx';
import { fmtPercent } from '../../utils/formatters.js';

export default function DefectProbabilityTrend({ data = [] }) {
  if (!data.length) return <EmptyState title="No probability trend" />;
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis tickFormatter={(v) => `${Math.round(v * 100)}%`} />
        <Tooltip formatter={(v) => fmtPercent(v)} />
        <Line dataKey="probability" stroke="#ff7a00" strokeWidth={3} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
