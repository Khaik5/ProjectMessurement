import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import EmptyState from '../common/EmptyState.jsx';

export default function CouplingDistributionChart({ data = [] }) {
  if (!data.length) return <EmptyState title="No coupling distribution" />;
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="bucket" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="count" fill="#0b1930" />
      </BarChart>
    </ResponsiveContainer>
  );
}
