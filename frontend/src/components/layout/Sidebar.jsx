import { BarChart3, BrainCircuit, Clock, FileText, LayoutDashboard, LogOut, Settings, UploadCloud, Users } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';

import { useAuth } from '../../auth/AuthContext.jsx';
import { useRole } from '../../auth/useRole.js';

const nav = [
  ['/dashboard', 'Dashboard', LayoutDashboard, 'DASHBOARD_VIEW', null],
  ['/metrics', 'Datasets', UploadCloud, ['DATASET_UPLOAD', 'DASHBOARD_VIEW'], ['Admin', 'Developer']],
  ['/models', 'Models', BrainCircuit, ['MODEL_TRAIN', 'MODEL_COMPARISON_VIEW'], ['Admin', 'Developer']],
  ['/history', 'History', Clock, 'HISTORY_VIEW', null],
  ['/reports', 'Reports', FileText, 'REPORT_VIEW', null],
  ['/settings', 'Settings', Settings, 'SYSTEM_SETTING', null],
  ['/users', 'Users', Users, 'USER_MANAGE', ['Admin']]
];

export default function Sidebar() {
  const { hasPermission, logout } = useAuth();
  const { hasRole } = useRole();
  const navigate = useNavigate();

  async function signOut() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark"><BarChart3 size={21} /></span>
        <div>
          <strong>DefectAI</strong>
          <span>Quality analytics</span>
        </div>
      </div>
      <nav>
        {nav
          .filter(([, , , permission, allowedRoles]) => {
            if (!hasPermission(permission)) return false;
            if (allowedRoles && !hasRole(allowedRoles)) return false;
            return true;
          })
          .map(([to, label, Icon]) => (
            <NavLink key={to} to={to} className={({ isActive }) => (isActive ? 'active' : '')}>
              <Icon size={20} />
              {label}
            </NavLink>
          ))}
      </nav>
      <button className="logout" onClick={signOut}><LogOut size={20} />Sign out</button>
    </aside>
  );
}
