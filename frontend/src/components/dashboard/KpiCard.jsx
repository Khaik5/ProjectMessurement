export default function KpiCard({ label, value, helper, icon: Icon }) {
  return (
    <div className="kpi-card">
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        {helper ? <small>{helper}</small> : null}
      </div>
      {Icon ? <Icon size={24} /> : null}
    </div>
  );
}
