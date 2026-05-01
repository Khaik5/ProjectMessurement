import { Navigate, useLocation } from 'react-router-dom';

import Loading from '../components/common/Loading.jsx';
import { useAuth } from './AuthContext.jsx';
import { useRole } from './useRole.js';

export default function ProtectedRoute({ children, permission, allowedRoles }) {
  const { user, loading, hasPermission } = useAuth();
  const { hasRole } = useRole();
  const location = useLocation();

  if (loading) return <Loading label="Checking session..." />;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  
  // Kiểm tra role nếu có allowedRoles
  if (allowedRoles && !hasRole(allowedRoles)) {
    return <Navigate to="/forbidden" replace />;
  }
  
  // Kiểm tra permission nếu có
  if (permission && !hasPermission(permission)) {
    return <Navigate to="/forbidden" replace />;
  }
  
  return children;
}

