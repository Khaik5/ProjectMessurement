import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import EmptyState from '../common/EmptyState.jsx';

export default function ChurnProbabilityChart({ data = [] }) {
  if (!data.length) return <EmptyState title="No churn/probability data" />;
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="module_name" hide />
        <YAxis />
        <Tooltip />
        <Bar dataKey="code_churn" fill="#94a3b8" />
        <Line dataKey="defect_probability" stroke="#c1121f" strokeWidth={3} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
