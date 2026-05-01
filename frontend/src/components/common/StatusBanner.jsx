import { CheckCircle2, Info, TriangleAlert } from 'lucide-react';

const icons = {
  success: CheckCircle2,
  warning: TriangleAlert,
  error: TriangleAlert,
  info: Info
};

export default function StatusBanner({ type = 'info', title, children, action }) {
  const Icon = icons[type] || Info;
  return (
    <div className={`status-banner status-${type}`}>
      <Icon size={18} />
      <div>
        {title ? <strong>{title}</strong> : null}
        {children ? <span>{children}</span> : null}
      </div>
      {action ? <div className="status-action">{action}</div> : null}
    </div>
  );
}
