import { BarChart3, BrainCircuit, Clock, FileText, LayoutDashboard, LogOut, Settings, UploadCloud, Users } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';

import { useAuth } from '../../auth/AuthContext.jsx';

const nav = [
  ['/dashboard', 'Dashboard', LayoutDashboard, 'DASHBOARD_VIEW'],
  ['/metrics', 'Metrics Explorer', UploadCloud, ['DATASET_UPLOAD', 'DASHBOARD_VIEW']],
  ['/models', 'AI Models', BrainCircuit, ['MODEL_TRAIN', 'MODEL_COMPARISON_VIEW']],
  ['/history', 'History', Clock, 'HISTORY_VIEW'],
  ['/reports', 'Reports', FileText, 'REPORT_VIEW'],
  ['/settings', 'Settings', Settings, 'SYSTEM_SETTING'],
  ['/users', 'Users', Users, 'USER_MANAGE']
];

export default function Sidebar() {
  const { hasPermission, logout } = useAuth();
  const navigate = useNavigate();

  async function signOut() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <BarChart3 />
        <div>
          <strong>DefectAI</strong>
          <span>AI Software Monitoring</span>
        </div>
      </div>
      <nav>
        {nav.filter(([, , , permission]) => hasPermission(permission)).map(([to, label, Icon]) => (
          <NavLink key={to} to={to} className={({ isActive }) => (isActive ? 'active' : '')}>
            <Icon size={20} />
            {label}
          </NavLink>
        ))}
      </nav>
      <button className="logout" onClick={signOut}><LogOut size={20} />Log Out</button>
    </aside>
  );
}
