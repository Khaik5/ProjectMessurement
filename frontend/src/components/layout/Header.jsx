import { Bell, CircleHelp, Search, UserCircle } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext.jsx';

const titles = {
  '/dashboard': 'Dashboard',
  '/metrics': 'Datasets',
  '/models': 'Models',
  '/reports': 'Reports',
  '/settings': 'Settings',
  '/users': 'Users',
  '/register': 'Create Account',
  '/history': 'History'
};

export default function Header({ pathname }) {
  const { user } = useAuth();
  const title = titles[pathname] || 'DefectAI';
  return (
    <header className="topbar">
      <div className="topbar-title">
        <span>DefectAI Platform</span>
        <h1>{title}</h1>
      </div>
      <div className="top-actions">
        <div className="project-pill">Project #{import.meta.env.VITE_DEFAULT_PROJECT_ID || 1}</div>
        <label className="header-search"><Search size={16} /><input placeholder="Search" /></label>
        <span className="header-icon"><Bell size={18} /></span>
        <span className="header-icon"><CircleHelp size={18} /></span>
        <div className="user-pill"><UserCircle size={28} /><span>{user?.username}</span></div>
      </div>
    </header>
  );
}
