import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer } from 'recharts';
import EmptyState from '../common/EmptyState.jsx';

export default function QualityRadarChart({ data = [] }) {
  if (!data.length) return <EmptyState title="No quality profile" />;
  return (
    <ResponsiveContainer width="100%" height={260}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="metric" />
        <PolarRadiusAxis domain={[0, 100]} />
        <Radar dataKey="score" stroke="#ff7a00" fill="#ff7a00" fillOpacity={0.3} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
