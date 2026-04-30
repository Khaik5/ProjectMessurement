import { Navigate, useLocation } from 'react-router-dom';

import Loading from '../components/common/Loading.jsx';
import { useAuth } from './AuthContext.jsx';

export default function ProtectedRoute({ children, permission }) {
  const { user, loading, hasPermission } = useAuth();
  const location = useLocation();

  if (loading) return <Loading label="Checking session..." />;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  if (permission && !hasPermission(permission)) return <Navigate to="/forbidden" replace />;
  return children;
}

