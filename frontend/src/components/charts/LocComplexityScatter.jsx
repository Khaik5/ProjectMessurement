import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts';
import EmptyState from '../common/EmptyState.jsx';

export default function LocComplexityScatter({ data = [] }) {
  if (!data.length) return <EmptyState title="No LOC/complexity data" />;
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ScatterChart>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="loc" name="LOC" />
        <YAxis dataKey="complexity" name="Complexity" />
        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
        <Scatter data={data} fill="#ff7a00" />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
