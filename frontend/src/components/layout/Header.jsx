import { Bell, CircleHelp, Search, UserCircle } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext.jsx';

const titles = {
  '/dashboard': 'Dashboard',
  '/metrics': 'Metrics Explorer',
  '/models': 'AI Model Management',
  '/reports': 'Reports & Analysis',
  '/settings': 'Settings',
  '/users': 'Users',
  '/register': 'Create Account',
  '/history': 'History'
};

export default function Header({ pathname }) {
  const { user } = useAuth();
  return (
    <header className="topbar">
      <h1>{titles[pathname] || 'DefectAI'}</h1>
      <div className="top-actions">
        <div className="project-pill">Project Selection</div>
        <label className="header-search"><Search size={16} /><input placeholder="Search modules..." /></label>
        <Bell size={22} />
        <CircleHelp size={22} />
        <div className="user-pill"><UserCircle size={28} /><span>{user?.username}</span></div>
      </div>
    </header>
  );
}
