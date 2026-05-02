import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import EmptyState from '../common/EmptyState.jsx';
import { fmtPercent, normalizeProbability } from '../../utils/formatters.js';

const colors = { LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#f97316', CRITICAL: '#dc2626' };

export default function TopRiskModulesBar({ data = [] }) {
  if (!data.length) return <EmptyState title="No risky modules" />;
  const rows = data.map((item) => ({ ...item, defect_probability: normalizeProbability(item.defect_probability) }));
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={rows} layout="vertical" margin={{ left: 40, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
        <YAxis dataKey="module_name" type="category" width={170} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v) => fmtPercent(v)} />
        <Bar dataKey="defect_probability" radius={[0, 4, 4, 0]}>
          {rows.map((entry) => <Cell key={entry.module_name} fill={colors[entry.risk_level] || '#ff7a00'} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
