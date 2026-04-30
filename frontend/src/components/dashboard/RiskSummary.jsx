import Badge from '../common/Badge.jsx';

export default function RiskSummary({ distribution = [] }) {
  return (
    <div className="risk-summary">
      {distribution.map((item) => (
        <div key={item.name}>
          <Badge level={item.name}>{item.name}</Badge>
          <strong>{item.value || 0}</strong>
        </div>
      ))}
    </div>
  );
}
