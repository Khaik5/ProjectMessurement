import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import EmptyState from '../common/EmptyState.jsx';

export default function RiskDistributionPie({ data = [] }) {
  if (!data.length || data.every((item) => !item.value)) return <EmptyState title="No risk distribution" description="Run dataset analysis to populate Predictions." />;
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={62} outerRadius={95} paddingAngle={3}>
          {data.map((item) => <Cell key={item.name} fill={item.color} />)}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
